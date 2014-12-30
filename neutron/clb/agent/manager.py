import time
from neutron import context
from neutron.agent import rpc as agent_rpc
from neutron.common import rpc
from neutron.openstack.common import log
from neutron.openstack.common import periodic_task
from neutron.openstack.common import loopingcall 
from neutron.openstack.common import importutils
from neutron.clb.common import topics
from neutron.clb.common import constants


LOG = log.getLogger(__name__)


class ClbPluginRpcapi(rpc.RpcProxy):
    """RPC calls from agent side to plugin side."""
    API_VERSION = '1.0'
    # history
    #   1.0 Initial version

    def __init__(self, topic, ctx, host):
        super(ClbPluginRpcapi, self).__init__(topic, self.API_VERSION)
        self.context = ctx
        self.host = host

    def get_all_load_balancers(self):
        return self.call(
            self.context,
            self.make_msg('get_all_load_balancers',
                          host=self.host),
            topic=self.topic
        )

    def notify_create_load_balancer_succ(self, load_balancer_id):
        return self.call(
            self.context,
            self.make_msg('notify_create_load_balancer_succ',
                          load_balancer_id=load_balancer_id),
            topic=self.topic
        )
    
    def notify_create_load_balancer_fail(self, load_balancer_id):
        return self.call(
            self.context,
            self.make_msg('notify_create_load_balancer_fail',
                          load_balancer_id=load_balancer_id),
            topic=self.topic
        )

    def notify_delete_load_balancer_succ(self, load_balancer_id):
        return self.call(
            self.context,
            self.make_msg('notify_delete_load_balancer_succ',
                          load_balancer_id=load_balancer_id),
            topic=self.topic
        )

    def notify_delete_load_balancer_fail(self, load_balancer_id):
        return self.call(
            self.context,
            self.make_msg('notify_delete_load_balancer_fail',
                          load_balancer_id=load_balancer_id),
            topic=self.topic
        )

    def notify_sync_load_balancer_succ(self, load_balancer_id):
        return self.call(
            self.context,
            self.make_msg('notify_sync_load_balancer_succ',
                          load_balancer_id=load_balancer_id),
            topic=self.topic
        )

    def notify_sync_load_balancer_fail(self, load_balancer_id):
        return self.call(
            self.context,
            self.make_msg('notify_sync_load_balancer_fail',
                          load_balancer_id=load_balancer_id),
            topic=self.topic
        )

    def notify_create_interface_succ(self, interface_id):
        return self.call(
            self.context,
            self.make_msg('notify_create_interface_succ',
                          interface_id=interface_id),
            topic=self.topic
        )
    
    def notify_create_interface_fail(self, interface_id):
        return self.call(
            self.context,
            self.make_msg('notify_create_interface_fail',
                          interface_id=interface_id),
            topic=self.topic
        )
    
    def notify_delete_interface_succ(self, interface_id):
        return self.call(
            self.context,
            self.make_msg('notify_delete_interface_succ',
                          interface_id=interface_id),
            topic=self.topic
        )
    
    def notify_delete_interface_fail(self, interface_id):
        return self.call(
            self.context,
            self.make_msg('notify_delete_interface_fail',
                          interface_id=interface_id),
            topic=self.topic
        )
    
    def notify_update_interface_succ(self, interface_id):
        return self.call(
            self.context,
            self.make_msg('notify_update_interface_succ',
                          interface_id=interface_id),
            topic=self.topic
        )
    
    def notify_update_interface_fail(self, interface_id):
        return self.call(
            self.context,
            self.make_msg('notify_update_interface_fail',
                          interface_id=interface_id),
            topic=self.topic
        ) 

    def notify_plug_interface_port(self, port_id):
        return self.call(
            self.context,
            self.make_msg('notify_plug_interface_port',
                          port_id=port_id,
                          host=self.host),
            topic=self.topic
        )

    def update_backend_health_state(self, backend_id, health_state,
                                    updated_at):
        return self.call(
            self.context,
            self.make_msg('update_backend_health_state',
                          backend_id=backend_id,
                          health_state=health_state,
                          updated_at=updated_at),
            topic=self.topic
        )


class ClbAgentManager(rpc.RpcCallback, periodic_task.PeriodicTasks):
    """plugin-to-agent RPC calls."""

    RPC_API_VERSION = '1.1'
    # history
    #   1.0 Initial version
    #   1.1 routes support
    #       - support subnet host-routes
    #       - suppport refresh_routes api

    def __init__(self, conf):
        super(ClbAgentManager, self).__init__()
    
        self.conf = conf
        self.context = context.get_admin_context_without_session()

        self.agent_state = {
            'host': self.conf.host,
            'topic': topics.CLB_AGENT_RPC,
            'binary': 'neutron-clb-agent',
            'agent_type': constants.CLB_AGENT_TYPE,
            'configurations': {},
            'start_flag': True
        }

        self.driver = None
        self.plugin_rpc = None
        self.state_rpc = None
        
    def init(self):
        self.plugin_rpc = ClbPluginRpcapi(
            topics.CLB_PLUGIN_RPC,
            self.context,
            self.conf.host
        )

        self.driver = self._load_driver()
        self.agent_state['configurations']['provider'] = self.driver.get_provider_name()

        self.state_rpc = agent_rpc.PluginReportStateAPI(topics.CLB_PLUGIN_RPC)
        report_interval = self.conf.AGENT.report_interval
        heartbeat = loopingcall.FixedIntervalLoopingCall(self._report_state)
        heartbeat.start(interval=report_interval)

        self.start_cleanup_on_init()

    def _load_driver(self):
        try:
            LOG.info("Load driver: %s" % self.conf.AGENT.driver)
            driver = importutils.import_object(
                self.conf.AGENT.driver,
                self.conf, self.plugin_rpc, self.context
            )
            return driver
        except ImportError:
            msg = "Error importing driver: %s" % self.conf.AGENT.driver
            LOG.error(msg)
            raise SystemExit(msg)

    def _report_state(self):
        try:
            self.state_rpc.report_state(self.context, self.agent_state)
            self.agent_state.pop('start_flag', None)
        except Exception:
            LOG.excption("Failed reporting state!")

    def create_load_balancer(self, context, load_balancer):
        try:
            lb = load_balancer
            self.driver.create_load_balancer(load_balancer)
            self.plugin_rpc.notify_create_load_balancer_succ(lb['id'])
            LOG.info("Load balancer %s successfully created" % lb['id'])
        except Exception:
            LOG.exception("Creating load balancer %s failed" % lb['id'])
            self.plugin_rpc.notify_create_load_balancer_fail(lb['id'])

    def delete_load_balancer(self, context, load_balancer):
        try:
            lb = load_balancer
            self.driver.delete_load_balancer(lb)
            self.plugin_rpc.notify_delete_load_balancer_succ(lb['id'])
            LOG.info("Load balancer %s successfully removed" % lb['id'])
        except Exception:
            LOG.exception("Deleting load balancer %s failed" % lb['id'])
            self.plugin_rpc.notify_delete_load_balancer_fail(lb['id'])

    def sync_load_balancer(self, context, load_balancer):
        try:
            lb = load_balancer
            self.driver.sync_load_balancer(lb)
            self.plugin_rpc.notify_sync_load_balancer_succ(lb['id'])
            LOG.info("Load balancer %s successfully syncronized" % lb['id'])
        except Exception:
            LOG.exception("Syncronizing load balancer %s failed" % lb['id'])
            self.plugin_rpc.notify_sync_load_balancer_fail(lb['id'])

    def refresh_routes(self, context, load_balancer):
        # this is a syncronized RPC call
        self.driver.refresh_routes(load_balancer)

    def create_interface(self, context, load_balancer, interface):
        try:
            self.driver.ensure_interface(load_balancer, interface)
            self.plugin_rpc.notify_plug_interface_port(interface['port_id'])
            self.plugin_rpc.notify_create_interface_succ(interface['id'])
            LOG.info("Interface %s successfully created" % interface['id'])
        except Exception:
            LOG.exception("Creating interface %s failed" % interface['id'])
            self.plugin_rpc.notify_create_interface_fail(interface['id'])

    def update_interface(self, context, load_balancer, interface):
        try:
            self.driver.ensure_interface(load_balancer, interface)
            self.plugin_rpc.notify_update_interface_succ(interface['id'])
            LOG.info("Interface %s successfully updated" % interface['id'])
        except Exception:
            LOG.exception("Updating interface %s failed" % interface['id'])
            self.plugin_rpc.notify_update_interface_fail(interface['id']) 
            
    def delete_interface(self, context, load_balancer, interface):
        try:
            self.driver.delete_interface(load_balancer, interface)
            self.plugin_rpc.notify_delete_interface_succ(interface['id'])
            LOG.info("Interface %s successfully removed" % interface['id'])
        except Exception:
            LOG.exception("Deleting interface %s failed" % interface['id'])
            self.plugin_rpc.notify_delete_interface_fail(interface['id'])   

    @periodic_task.periodic_task(spacing=6)
    def collect_stats(self, context):
        self.driver.collect_stats()

    ######################################################
    # Cleanup worker at agent startup
    ######################################################

    def _get_load_balancers_hosted_by_this_agent(self):
        # need to retry in case Neutron API Server is not prepared
        # on physical host booting.
        count = 1
        while count <= 3:
            try:
                return self.plugin_rpc.get_all_load_balancers()
            except Exception as e:
                LOG.error("Get load balancers info failed", e)
            time.sleep(3)
            count += 1

    def _sync_vif_state(self, lb, vif):
        if vif['task_state'] == constants.TASK_CREATING:
            self.create_interface(self.context, lb, vif)
        elif vif['task_state'] == constants.TASK_DELETING:
            self.delete_interface(self.context, lb, vif)
        elif vif['task_state'] == constants.TASK_UPDATING:
            self.update_interface(self.context, lb, vif)
        elif vif['task_state'] == constants.TASK_NONE:
            if vif['state'] != constants.STATE_ERROR:
                self.create_interface(self.context, lb, vif)
        else:
            LOG.warn("vif-%(id)s: unknown task state: "
                     "%(task_state)s" % vif)

    def _sync_vifs_state(self, lb, vifs):
        for vif in vifs:
            self._sync_vif_state(lb, vif)

    def _sync_lb_state(self, lb):
        if lb['task_state'] == constants.TASK_CREATING:
            self.create_load_balancer(self.context, lb)
        elif lb['task_state'] == constants.TASK_DELETING:
            self.delete_load_balancer(self.context, lb)
        elif lb['task_state'] == constants.TASK_SYNCRONIZING:
            self.sync_load_balancer(self.context, lb)
            self._sync_vifs_state(lb, lb['interfaces'])
        elif lb['task_state'] == constants.TASK_NONE:
            if lb['state'] != constants.STATE_ERROR:
                self.sync_load_balancer(self.context, lb)
                self._sync_vifs_state(lb, lb['interfaces'])
        else:
            LOG.warn("lb-%(id)s: unknown task state: "
                     "%(task_state)s" % lb)

    def _sync_lbs_state(self, lbs):
        for lb in lbs:
            self._sync_lb_state(lb)

    def start_cleanup_on_init(self):
        lbs = self._get_load_balancers_hosted_by_this_agent()
        if lbs is not None:
            self.driver.start_cleanup_on_init(lbs)
            self._sync_lbs_state(lbs)