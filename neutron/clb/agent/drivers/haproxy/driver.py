import os
import shutil
import socket

from oslo.config.cfg import CONF
from neutron.agent.linux import ip_lib
from neutron.agent.linux import utils as agent_utils
from neutron.openstack.common import log
from neutron.clb.common import constants
from neutron.openstack.common import timeutils
from neutron.clb.agent.drivers.haproxy import haproxy_config
from neutron.clb.agent.drivers.haproxy import haproxy_stats
from neutron.clb.agent.drivers.haproxy import vif as vif_driver
from neutron.clb.agent.drivers.haproxy import utils


LOG = log.getLogger(__name__)


class HaproxyDriver(object):
    
    def __init__(self, conf, plugin_rpc, context):
        self.plugin_rpc = plugin_rpc
        self.root_helper = CONF.AGENT.root_helper

        self.ip_wrap = ip_lib.IPWrapper(self.root_helper)
        self.vif = vif_driver.VIF()

        utils.ensure_state_dir()
        
    @staticmethod
    def get_provider_name():
        return constants.PROVIDER_HAPROXY

    def _lb_dir_clean_up(self, lb_id):
        lb_dir_path = utils.get_load_balancer_dir(lb_id)
        if os.path.isdir(lb_dir_path):
            try:
                shutil.rmtree(lb_dir_path)
            except Exception as e:
                LOG.warn("lb-%s: remove directory failed: %s" % (lb_id, e))

    def _lb_netns_clean_up(self, lb_id):
        netns = utils.get_namespace(lb_id)

        if not self.ip_wrap.netns.exists(netns):
            return

        ip_wrap = ip_lib.IPWrapper(self.root_helper, netns)
        # remove unexpected remained interfaces
        try:
            device_names = ip_wrap.get_devices(exclude_loopback=True)
        except Exception as e:
            LOG.warn("lb-%s: get network devices failed: %s" % (lb_id, e))
            return

        for dev_name in device_names:
            try:
                LOG.info("lb-%s: remove network device %s" % (lb_id, dev_name))
                self.vif.unplug(netns, dev_name)
            except Exception as e:
                LOG.warn("lb-%s: remove network device %s failed: %s"
                         % (lb_id, dev_name, e))

        try:
            ip_wrap.garbage_collect_namespace()
        except Exception as e:
            LOG.warn("lb-%s: remove network namespace failed: %s" % (lb_id, e))

    def _lb_process_exists(self, lb_id):
        netns = utils.get_namespace(lb_id)
        sock_file = utils.get_sock_file_path(lb_id)

        if self.ip_wrap.netns.exists(netns) and os.path.exists(sock_file):
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(sock_file)
                return True
            except socket.error:
                LOG.warn("lb-%s: Haproxy process killed but socket file "
                         "remained" % lb_id)
        return False

    def _lb_process_kill(self, lb_id):
        try:
            pid_file = utils.get_pid_file_path(lb_id)
            sock_file = utils.get_sock_file_path(lb_id)
            pid = utils.get_pid(pid_file)
            try:
                # this will leave socket and pid file unremoved
                cmd = ['kill', '-9', pid]
                agent_utils.execute(cmd, self.root_helper)
                return 0
            except Exception as e:
                LOG.warn("lb-%s: kill Haproxy process failed: %s" % (lb_id, e))
        except IOError as e:
            LOG.warn("lb-%s: read pid failed: %s" % (lb_id, e.strerror))
        return -1

    def _lb_process_spawn(self, lb_id):
        netns = utils.get_namespace(lb_id)
        cfg_file = utils.get_cfg_file_path(lb_id)
        pid_file = utils.get_pid_file_path(lb_id)
        cmd = [CONF.Haproxy.haproxy_bin, '-D', '-f', cfg_file, '-p', pid_file]
        ip_wrap = ip_lib.IPWrapper(self.root_helper, netns)

        try:
            # TODO: check haproxy configuration before start
            LOG.info("lb-%s: %s" % (lb_id, ' '.join(cmd)))
            ip_wrap.netns.execute(cmd)
            return 0
        except Exception as e:
            LOG.warn("lb-%s: spawn haproxy process failed: %s" % (lb_id, e))
        return -1

    def _lb_process_reload(self, lb_id):
        netns = utils.get_namespace(lb_id)
        cfg_file = utils.get_cfg_file_path(lb_id)
        pid_file = utils.get_pid_file_path(lb_id)
        ip_wrap = ip_lib.IPWrapper(self.root_helper, netns)

        try:
            pid = utils.get_pid(pid_file)
            cmd = [CONF.Haproxy.haproxy_bin, '-D', '-f', cfg_file,
                   '-p', pid_file, '-sf', pid]
            try:
                # TODO: check haproxy configuration before start
                LOG.info("lb-%s: %s" % (lb_id, ' '.join(cmd)))
                ip_wrap.netns.execute(cmd)
                return 0
            except Exception as e:
                LOG.warn("lb-%s: reload configuration failed: %s" % (lb_id, e))
        except IOError as e:
            LOG.warn("lb-%s: read pid failed: %s" % (lb_id, e.strerror))
        return -1

    def create_load_balancer(self, lb):
        """Create namespace and directory for load balancer.
        :param lb: (dict) load balancer data, actually only id is need
        """
        LOG.debug("create_load_balancer(%(id)s).start" % lb)

        netns = utils.get_namespace(lb['id'])

        self.ip_wrap.ensure_namespace(netns)
        utils.ensure_load_balancer_dir(lb['id'])

        LOG.debug("create_load_balancer(%(id)s).end" % lb)

    def delete_load_balancer(self, lb):
        """Remove load balancer, we only need to remove related Haproxy
        process, directory, and namespace.
        This will always return success.
        :param lb: (dict) load balancer data
        """
        LOG.debug("delete_load_balancer(%(id)s).start" % lb)

        # If Haproxy process exists and could not be killed, do not remove
        # directory (so that administrators can easily cleanup) and
        # namespace (for this would also failed).
        #
        # Since interfaces has been removed before deleting load balancer,
        # hanging process would make no other effect, only consume little
        # CPU power and memory.
        #
        if self._lb_process_exists(lb['id']):
            if self._lb_process_kill(lb['id']) == -1:
                return
        self._lb_netns_clean_up(lb['id'])
        self._lb_dir_clean_up(lb['id'])

        LOG.debug("delete_load_balancer(%(id)s).end" % lb)

    def _need_to_start_lb_process(self, lb):
        """Determine whether we need to start Haproxy process for
        load balancer or not.
        :return need_to_start: (bool)
        """
        enabled_listeners = [listener for listener in lb['listeners']
                             if listener['enabled']]
        for listener in enabled_listeners:
            for backend in listener['backends']:
                if backend['enabled']:
                    return True
        return False

    def _sync_load_balancer(self, lb):
        need_start = self._need_to_start_lb_process(lb)
        process_exist = self._lb_process_exists(lb['id'])

        # try to code without too much indentation
        # only four cases

        if not need_start and not process_exist:
            # we are done
            _clean_up_sock_file(lb['id'])
            _clean_up_pid_file(lb['id'])
            return

        if not need_start and process_exist:
            # kill existing process
            if self._lb_process_kill(lb['id']) == 0:
                _clean_up_sock_file(lb['id'])
                _clean_up_pid_file(lb['id'])
                return

        if need_start and not process_exist:
            # spawn a new process
            _save_certificates(lb)
            _save_haproxy_config(lb)
            if self._lb_process_spawn(lb['id']) == 0:
                return

        if need_start and process_exist:
            _save_certificates(lb)
            _save_haproxy_config(lb)
            # try to reload new configuration
            if self._lb_process_reload(lb['id']) == 0:
                return

            # if failed, kill old process and spawn a new one
            if self._lb_process_kill(lb['id']) == 0:
                if self._lb_process_spawn(lb['id']) == 0:
                    return

        raise RuntimeError

    def sync_load_balancer(self, lb):
        """Syncronizing load balancer configuration. Directory and network
        namespace will always exist, but Haproxy process may by reloaded,
        respawned, or killed.
        If any error has happened, raise a RuntimeError exception.
        :param lb(dict): load balancer data
        """
        LOG.debug("sync_load_balancer(%(id)s).start" % lb)

        netns = utils.get_namespace(lb['id'])
        self.ip_wrap.ensure_namespace(netns)

        utils.ensure_load_balancer_dir(lb['id'])

        self._sync_load_balancer(lb)

        LOG.debug("sync_load_balancer(%(id)s).end" % lb)

    def set_default_gateway(self, lb):
        netns = utils.get_namespace(lb['id'])

        vifs = [vif for vif in lb['interfaces']
                if (vif['state'] != constants.STATE_ERROR and
                    vif['task_state'] != constants.TASK_DELETING)]

        public_vifs = [vif for vif in vifs if vif['is_public']]

        if public_vifs:
            for vif in public_vifs:
                port = vif['port']
                for fixed_ip in port['fixed_ips']:
                    gateway_ip = fixed_ip['subnet'].get('gateway_ip')
                    if gateway_ip:
                        self.vif.add_default_route(netns, gateway_ip)
                        return
            LOG.warn("lb-%(id)s: not any gateway ip found in public interfaces"
                     % lb)
        else:
            private_vifs = [vif for vif in vifs if not vif['is_public']]
            for vif in private_vifs:
                port = vif['port']
                for fixed_ip in port['fixed_ips']:
                    gateway_ip = fixed_ip['subnet'].get('gateway_ip')
                    if gateway_ip:
                        self.vif.add_default_route(netns, gateway_ip)
                        return
            LOG.warn("lb-%(id)s: default gateway ip could not be set" % lb)

    def refresh_routes(self, lb):
        netns = utils.get_namespace(lb['id'])
        for vif in lb['interfaces']:
            if (vif['state'] != constants.STATE_ERROR and
                vif['task_state'] != constants.TASK_DELETING):
                port = vif['port']
                vif_name = self.vif.get_vif_name(self, port)
                self.vif.add_route(netns, vif_name, port)
        self.set_default_gateway(lb)

    def ensure_interface(self, lb, vif):
        """Ensure existence and configuration of load balancer interface.
        :param lb: (dict) load balancer data
        :param vif: (dict) load balancer interface data
        """
        LOG.debug("ensure_interface(%(id)s).start" % vif)

        port = vif['port']
        vif_name = self.vif.get_vif_name(port)
        netns = utils.get_namespace(lb['id'])

        # If interface already exists, call vif.plug
        # will just do nothing.
        self.vif.plug(netns, vif_name, port)
        self.vif.setup_ip_addresses(netns, vif_name, port)
        self.vif.add_routes(netns, vif_name, port)
        self.vif.setup_rate_limit(netns, vif)
        self.set_default_gateway(lb)

        LOG.debug("ensure_interface(%(id)s).end" % vif)

    def delete_interface(self, lb, vif):
        """Remove load balancer interface and relating route rules.
        :param lb: load balancer data
        :param vif: load balancer interface data
        """
        LOG.debug("delete_interface(%(id)s).start" % vif)

        netns = utils.get_namespace(lb['id'])
        port = vif['port']
        vif_name = self.vif.get_vif_name(port)

        self.vif.unplug(netns, vif_name)
        self.set_default_gateway(lb)

        LOG.debug("delete_interface(%(id)s).end" % vif)

    def collect_stats(self):
        """Collect statistic data for all Haproxy processes. In this Havana
        release we only use the data to update backend health state."""
        lb_ids = os.listdir(utils.get_state_dir())
        for lb_id in lb_ids:
            try:
                backend_stats = haproxy_stats.collect_lb_stats(lb_id)
                _update_backend_health_state(self.plugin_rpc, backend_stats)
            except Exception as e:
                msg = ("lb-%s: collecting statistic data failed: %s" % (lb_id, e))
                LOG.warn(msg)

    ###############################################################
    # Cleanup on agent startup.
    ###############################################################

    def _start_netns_cleanup(self, lbs):
        netns_list = self.ip_wrap.get_namespaces(self.root_helper)
        lb_ids = [netns[len(constants.NS_PREFIX):]
                  for netns in netns_list
                  if netns.startswith(constants.NS_PREFIX)]
        lb_ids_to_remove = [lb_id for lb_id in lb_ids if lb_id not in lbs]
        for lb_id in lb_ids_to_remove:
            self._lb_netns_clean_up(lb_id)

    def _start_dir_and_process_cleanup(self, lbs):
        lb_ids = os.listdir(CONF.clb_state_path)
        lb_ids_to_remove = [lb_id for lb_id in lb_ids if lb_id not in lbs]
        for lb_id in lb_ids_to_remove:
            if self._lb_process_exists(lb_id):
                if self._lb_process_kill(lb_id) == -1:
                    continue
            self._lb_dir_clean_up(lb_id)

    def start_cleanup_on_init(self, lbs):
        """Cleanup not used Haproxy processes, directories, interfaces and
        namespaces.
        :param lbs: (dict) detailed data of load balancers hosted by this agent
        """
        self._start_dir_and_process_cleanup(lbs)
        self._start_netns_cleanup(lbs)


def _save_certificates(lb):
    lb_dir = utils.get_load_balancer_dir(lb['id'])
    for certificate in lb['certificates']:
        pem_file_path = os.path.join(lb_dir, '%s.pem' % certificate['id'])
        crt = certificate['certificate'].strip()
        key = certificate['key'].strip()
        agent_utils.replace_file(pem_file_path, '%s\n%s' % (crt, key))


def _save_haproxy_config(lb):
    cfg_file_path = utils.get_cfg_file_path(lb['id'])
    cfg_text = haproxy_config.get_haproxy_config_text(lb)
    agent_utils.replace_file(cfg_file_path, cfg_text)


def _update_backend_health_state(plugin_rpc, backend_stats):
    for backend_id, stats in backend_stats.iteritems():
        try:
            health_state = stats[constants.STATS_STATUS]
            updated_at = timeutils.strtime()
            plugin_rpc.update_backend_health_state(backend_id,
                                                   health_state,
                                                   updated_at)
        except Exception as e:
            msg = ("Updating health state of backend %s through RPC "
                   "failed: %s")
            LOG.debug(msg % (backend_id, e))


def _clean_up_sock_file(lb_id):
    sock_file = utils.get_sock_file_path(lb_id)
    if os.path.exists(sock_file):
        try:
            LOG.info("lb-%s: remove socket file" % lb_id)
            os.remove(sock_file)
        except OSError as e:
            LOG.warn("lb-%s: remove socket file failed: %s"
                     % (lb_id, e.strerror))


def _clean_up_pid_file(lb_id):
    pid_file = utils.get_pid_file_path(lb_id)
    if os.path.exists(pid_file):
        try:
            LOG.info("lb-%s: remove pid file" % lb_id)
            os.remove(pid_file)
        except OSError as e:
            LOG.warn("lb-%s: remove pid file failed: %s"
                     % (lb_id, pid_file))


def _clean_up_cfg_file(lb_id):
    cfg_file = utils.get_cfg_file_path(lb_id)
    if os.path.exists(cfg_file):
        try:
            LOG.info("lb-%s: remove config file" % lb_id)
            os.remove(cfg_file)
        except OSError as e:
            LOG.warn("lb-%s: remove config file failed: %s"
                     % (lb_id, e.strerror))