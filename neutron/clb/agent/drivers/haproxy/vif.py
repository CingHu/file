#coding: utf-8
import json
import netaddr
from oslo.config.cfg import CONF
from neutron.openstack.common import importutils
from neutron.openstack.common import log
from neutron.agent.linux import ip_lib
from neutron.agent.linux import utils

LOG = log.getLogger(__name__)


# NOTE(from markmcclain) For compliance with interface.py which expects objects
class PortWrap(object):

    def __init__(self, d):
        self.__dict__.update(d)
    
    def __getitem__(self, key):
        return self.__dict__[key] 


class VIF(object):
    """Class to group load balancer interface operations.
    :note :setup_rate_limit: only support OVS interface driver.
    """

    def __init__(self):
        self.root_helper = CONF.AGENT.root_helper
        self.arp_count = CONF.Haproxy.send_gratuitous_arp
        
        self.ip = ip_lib.IPWrapper(self.root_helper)  

        try:
            self.vif_driver = importutils.import_object(
                CONF.AGENT.interface_driver,
                CONF
            )
        except ImportError:
            msg = "Error importing interface driver: %s"
            LOG.error(msg)
            raise SystemExit(msg % CONF.AGENT.interface_driver)

    def _send_gratuitous_arp(self, namespace, vif_name, ip_address, count):
        cmd = ['arping', '-U', '-I', vif_name, '-c', count, ip_address]
        ip_wrapper = ip_lib.IPWrapper(self.root_helper, namespace=namespace)
        ip_wrapper.netns.execute(cmd, check_exit_code=False)

    def _add_route(self, namespace, vif_name, network, netmask, gateway_ip): 
        cmd = ['route', 'add', '-net', network, 'netmask', netmask, 
               'gw', gateway_ip, 'dev', vif_name]
        ip_wrapper = ip_lib.IPWrapper(self.root_helper, namespace=namespace)
        ip_wrapper.netns.execute(cmd, check_exit_code=False)

    def _del_route(self, namespace, vif_name, network, netmask):
        cmd = ['route', 'del', '-net', network, 'netmask', netmask,
               'dev', vif_name]
        ip_wrapper = ip_lib.IPWrapper(self.root_helper, namespace=namespace)
        ip_wrapper.netns.execute(cmd, check_exit_code=False)

    def _add_default_route(self, netns, vif_name, gateway_ip):
        cmd = ['route', 'add', 'default', 'gw', gateway_ip]
        ip_wrap = ip_lib.IPWrapper(self.root_helper, namespace=netns)
        ip_wrap.netns.execute(cmd, check_exit_code=False)

    def add_route(self, namespace, vif_name, fixed_ip):
        subnet = fixed_ip['subnet']
        gateway_ip = subnet.get('gateway_ip')
        host_routes = subnet.get('host_routes', [])

        if not gateway_ip:
            return

        network = str(netaddr.IPNetwork(subnet['cidr']).network)
        netmask = str(netaddr.IPNetwork(subnet['cidr']).netmask)
        self._add_route(namespace, vif_name, network, netmask, gateway_ip)

        for host_route in host_routes:
            network = str(netaddr.IPNetwork(host_route['destination']).network)
            netmask = str(netaddr.IPNetwork(host_route['destination']).netmask)
            self._add_route(namespace, vif_name, network, netmask,
                            host_route['nexthop'])

        if self.arp_count > 0:
            ip = fixed_ip['ip_address']
            self._send_gratuitous_arp(namespace, vif_name, ip, self.arp_count)
    
    def del_route(self, namespace, vif_name, fixed_ip):
        gateway_ip = fixed_ip['subnet'].get('gateway_ip')
        if not gateway_ip:
            return

        network = str(netaddr.IPNetwork(fixed_ip['subnet']['cidr']).network)
        netmask = str(netaddr.IPNetwork(fixed_ip['subnet']['cidr']).netmask)

        self._del_route(namespace, vif_name, network, netmask)

    def add_routes(self, namespace, vif_name, port):
        for fixed_ip in port['fixed_ips']:
            self.add_route(namespace, vif_name, fixed_ip)

    def del_routes(self, namespace, vif_name, port):
        for fixed_ip in port['fixed_ips']:
            self.del_route(namespace, vif_name, fixed_ip)

    def add_default_route(self, netns, gateway_ip):
        cmd = ['route', 'add', 'default', 'gw', gateway_ip]
        ip_wrap = ip_lib.IPWrapper(self.root_helper, namespace=netns)
        ip_wrap.netns.execute(cmd, check_exit_code=False)

    def _init_l3(self, dev_name, ip_cidrs, namespace=None):
        dev = ip_lib.IPDevice(dev_name, self.root_helper,
                              namespace=namespace)
        
        removed_ip_cidrs = {}
        for addr in dev.addr.list(scope='global', filters=['permanent']):
            removed_ip_cidrs[addr['cidr']] = addr['ip_version']

        added_ip_cidrs = []
        for ip_cidr in ip_cidrs:
            if ip_cidr in removed_ip_cidrs:
                del removed_ip_cidrs[ip_cidr]
            else:
                added_ip_cidrs.append(ip_cidr)

        for ip_cidr, ip_version in removed_ip_cidrs.items():
            dev.addr.delete(ip_version, ip_cidr)
        
        for ip_cidr in added_ip_cidrs:
            net = netaddr.IPNetwork(ip_cidr)
            dev.addr.add(net.version, ip_cidr, str(net.broadcast))

    def setup_ip_addresses(self, namespace, vif_name, port):
        cidrs = []

        for fixed_ip in port['fixed_ips']:
            prefixlen = netaddr.IPNetwork(fixed_ip['subnet']['cidr']).prefixlen
            cidr = '%s/%s' % (fixed_ip['ip_address'], prefixlen)
            cidrs.append(cidr)

        self._init_l3(vif_name, cidrs, namespace=namespace)

    def plug(self, netns, vif_name, port):
        if ip_lib.device_exists(vif_name, self.root_helper, netns):
            LOG.warn("Reuse load balancer interface %s" % vif_name)
        else:
            self.vif_driver.plug(
                port['network_id'],
                port['id'],
                vif_name,
                port['mac_address'],
                namespace=netns
            )

    def unplug(self, netns, vif_name):
        self.vif_driver.unplug(vif_name, namespace=netns)

    def get_vif_name(self, port):
        return self.vif_driver.get_device_name(PortWrap(port))

    ######################################################
    # Open vSwitch interface and port QoS rate limiting 
    ######################################################

    def _ovs_get_interface_uuid(self, port_id):
        """Get OVS port interface uuid through load balancer interface id.
        :param port_id: load balancer interface id
        """
        args = ['ovs-vsctl', '--timeout=2',
                '--columns=_uuid',
                'find', 'Interface',
                'external_ids:iface-id="%s"' % port_id]
        result = utils.execute(args, root_helper=self.root_helper)

        if not result:
            msg = "Open vSwitch interface for Neutron port %s not found"
            raise RuntimeError(msg % port_id)

        ovs_interface_uuid = result.split(':')[1].strip()

        return ovs_interface_uuid

    def _ovs_get_port_qos_info(self, ovs_interface_uuid):
        args = ['ovs-vsctl', '--timeout=2',
                '--columns=_uuid,qos',
                'find', 'Port',
                'interfaces=[%s]' % ovs_interface_uuid]
        result = utils.execute(args, root_helper=self.root_helper)

        if not result:
            msg = "Open vSwitch port for interface %s not found"
            raise RuntimeError(msg % ovs_interface_uuid)

        lines = result.splitlines()
        ovs_port_uuid = lines[0].split(':')[1].strip()
        ovs_qos_uuid = lines[1].split(':')[1].strip()
        
        qos_info = {
            'port': ovs_port_uuid,
            'qos': None,
            'queue': None,
        }
        
        if len(ovs_qos_uuid) == 36:
            qos_info['qos'] = ovs_qos_uuid
            args = ['ovs-vsctl', '--timeout=2', '--columns=queues',
                    'list', 'qos', qos_info['qos']]
            output = utils.execute(args, root_helper=self.root_helper)
            queues = output.split(':')[1].strip()
            if len(queues) > 3:
                qos_info['queue'] = queues[1:-1].split('=')[1]

        return qos_info

    def _ovs_set_interface_ingress(self, interface_uuid, inbound_limit):
        """Set up ingress rate limiting through OVS interface ingress
        policy.
        :param inbound_limit: unit is KiB (1024 bytes/second)
        """
        if inbound_limit < 0:
            raise ValueError("inbound_limit is negative.")
        
        burst = 0.1 * inbound_limit * 1024
        if burst < CONF.network_device_mtu:
            burst = CONF.network_device_mtu
        
        ingress = int(inbound_limit * 1024.0 * 8.0 / 1000.0)
        ingress_burst = int(burst * 8.0 / 1000.0)
        
        args = ['ovs-vsctl', '--timeout=2',
                'set', 'Interface', interface_uuid,
                'ingress_policing_rate=%d' % ingress]
        utils.execute(args, root_helper=self.root_helper)
        
        args = ['ovs-vsctl', '--timeout=2',
                'set', 'Interface', interface_uuid,
                'ingress_policing_burst=%d' % ingress_burst]
        utils.execute(args, root_helper=self.root_helper)

    def _ovs_set_port_qos(self, qos_info, outbound_limit):
        """Set up egress rate limiting through OVS port QoS.
        :param qos_info: (dict) uuid of Port, QoS and Queue
        :param outbound_limit: unit is KiB (1024 bytes/second)
        """
        if outbound_limit < 0:
            raise ValueError("outbound_limit is negative.")
        
        # remove old qos & queue
        if qos_info['qos']:
            args = ['ovs-vsctl', '--timeout=2',
                    '--', 'destroy', 'qos', qos_info['qos'],
                    '--', 'clear', 'port', qos_info['port'], 'qos']

            if qos_info['queue']:
                args = args + ['--', 'destroy', 'queue', qos_info['queue']]

            utils.execute(args, root_helper=self.root_helper)
        
        if outbound_limit == 0:
            return
        
        # create new qos & queue, unit is bit/s    
        out_max_rate = outbound_limit * 1024 * 8 

        args = ['ovs-vsctl', '--timeout=2', 
                '--', 'set', 'Port', qos_info['port'], 'qos=@newqos',
                '--', '--id=@newqos',
                'create', 'QoS', 'type=linux-htb',
                'other-config:max-rate=%d' % out_max_rate,
                'queues=0=@q0',
                '--', '--id=@q0', 
                'create', 'Queue',
                'other-config:max-rate=%d' % out_max_rate]

        utils.execute(args, root_helper=self.root_helper)

    def setup_rate_limit(self, namespace, interface):
        """Rate limit settings for load balancer interfaces.
        Note: this only works for OVS interface driver.
        :param namespace: load balancer network namespace
        :param interface: complete interface information
        """
        port = interface['port']
        
        ovs_interface_uuid = self._ovs_get_interface_uuid(port['id'])

        if 'inbound_limit' in interface:
            self._ovs_set_interface_ingress(ovs_interface_uuid,
                                            interface['inbound_limit'])

        if 'outbound_limit' in interface:
            qos_info = self._ovs_get_port_qos_info(ovs_interface_uuid)
            self._ovs_set_port_qos(qos_info, interface['outbound_limit'])
