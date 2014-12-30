#!/usr/bin/env python
# Copyright (C) 2014 CentecNetworks, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# @author: Yi Zhao, Centec Networks, Inc.

import hashlib
import json
from neutron.agent.linux import utils
from neutron.common import constants
from neutron.extensions import portbindings
from neutron.openstack.common import context
from neutron.openstack.common import log, loopingcall
from neutron.common import rpc as n_rpc
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2.drivers import mech_agent
import os
import shlex

from neutron.plugins.ml2.drivers.centec.config.constants import CentecConstant
from neutron.plugins.ml2.drivers.centec.config.ml2_config import CentecML2MechConfig,\
    MANAGER_VLAN_ALLOC_TYPE_TENANT
from neutron.plugins.ml2.drivers.centec.lib.centec_daemon import CentecDaemon
from neutron.plugins.ml2.drivers.centec.lib.centec_lib import CentecLib
from neutron.plugins.ml2.drivers.centec.mechanism_driver.protocol_driver.json_rpc_driver import JsonRpcDriver
from neutron.plugins.ml2.drivers.centec.mechanism_driver.protocol_driver.xmpp_driver import XmppDriver


LOG = log.getLogger(__name__)

CENTEC_RPC_TOPIC = 'centec_rpc'


class CentecRpcCallbacks(n_rpc.RpcCallback):
    """Centec callback."""

    RPC_API_VERSION = '1.0'

    def __init__(self, rpc_handler):
        """
        Init
        :param rpc_handler: rpc handler
        """
        super(CentecRpcCallbacks, self).__init__()
        self.rpc_handler = rpc_handler

    def get_switch_local_vlan_id(self, rpc_context, **kwargs):
        """
        Get switch local vlan id
        :param rpc_context: rpc context
        """
        port_id = kwargs.get('port_id')
        host_name = kwargs.get('host_name')
        if self.rpc_handler is None:
            return
        context = {'port_id': str(port_id), 'host_name': str(host_name)}

        response = None
        try:
            response = self.rpc_handler.get_switch_local_vlan_id(context)
        except:
            pass
        return response

    def get_connected_switch(self, rpc_context, **kwargs):
        """
        Get connected switch
        :param rpc_context: rpc context
        """
        host_name = kwargs.get('host_name')
        if self.rpc_handler is None:
            return
        context = {'host_name': str(host_name)}

        response = None
        try:
            response = self.rpc_handler.get_connected_switch(context)
        except:
            pass
        return response


class CentecTorMechanismDriver(mech_agent.SimpleAgentMechanismDriverBase):
    """
    Centec TOR switch mechanism driver
    """
    centec_manger_name = "centec-cloud-switch-manager"
    monitor_interval = 10
    root_helper = "sudo"
    pid_file = '/var/run/%s.pid' % centec_manger_name
    rpc_type = 'json-rpc'
    rpc_handler = None

    def __init__(self):
        """
        Init
        Read config
        Start centec-cloud-switch-manager
        """
        LOG.info(_("Centec mech driver init"))
        self.read_config()

        if self.manager_vlan_alloc_type == MANAGER_VLAN_ALLOC_TYPE_TENANT:
            LOG.info('Vlan alloc type: tenant')
            super(CentecTorMechanismDriver, self).__init__(
                                                             CentecConstant.AGENT_TYPE_DVR,
                                                             portbindings.VIF_TYPE_OVS,
                                                             {portbindings.CAP_PORT_FILTER: True,
                                                              portbindings.OVS_HYBRID_PLUG: True})
        else:
            LOG.info('Vlan alloc type: network')
            super(CentecTorMechanismDriver, self).__init__(
                                                           CentecConstant.AGENT_TYPE_LINUXBRIDGE,
                                                           portbindings.VIF_TYPE_BRIDGE,
                                                           {portbindings.CAP_PORT_FILTER: True})

    def read_config(self):
        """
        Read configure files
        """
        ml2_conf = CentecML2MechConfig()
        CentecTorMechanismDriver.root_helper = ml2_conf.get_manager_root_helper()
        self.manager_ip = ml2_conf.get_manager_rpc_ip()
        self.manager_nb_port = ml2_conf.get_manager_nb_port()
        self.manager_sb_port = ml2_conf.get_manager_sb_port()
        self.manager_auto_start = ml2_conf.get_manager_auto_start()
        self.manager_remote_debug = ml2_conf.get_manager_remote_debug()
        self.manager_verbose = ml2_conf.get_manager_verbose()
        self.manager_debug = ml2_conf.get_manager_debug()
        self.manager_vlan_alloc_type = ml2_conf.get_manager_vlan_alloc_type()
        self.manager_log_file = ml2_conf.get_manager_log_file()
        self.centec_manager_args = ["--centec-detach",
                                    "--centec-nb-port", str(self.manager_nb_port),
                                    "--centec-sb-port", str(self.manager_sb_port),
#                                    "--centec-vlan-alloc-type", str(self.manager_vlan_alloc_type),
                                    "--centec-log-file",
                                    str(self.manager_log_file)]
        if self.manager_remote_debug:
            self.centec_manager_args = self.centec_manager_args + ['--centec-remote-debug']
        if self.manager_verbose:
            self.centec_manager_args = self.centec_manager_args + ['--centec-verbose']
        if self.manager_debug:
            self.centec_manager_args = self.centec_manager_args + ['--centec-debug']
        self.centec_manager_args = self.centec_manager_args + ml2_conf.config_files        

    def run_centec_manager(self, args):
        """
        start new centec manager
        :param args: arguments
        """
        cmds = [CentecTorMechanismDriver.centec_manger_name] + args
        if CentecTorMechanismDriver.root_helper:
            cmds = shlex.split(CentecTorMechanismDriver.root_helper) + cmds
            cmds = map(str, cmds)
        cmd = ' '.join(cmds)
        try:
            ret = os.system(cmd.strip())
            if ret != 0:
                msg = os.strerror(ret >> 8)
                LOG.error(_("Can't start centec cloud manager, error message: %s"), msg)
                raise Exception
        except Exception as e:
            LOG.error(_("Unable to execute %(cmd)s. "
                        "Exception: %(exception)s"),
                      {'cmd': cmd, 'exception': e})
            # raise e

    def _centec_manager_monitor(self, args):
        """
        Check centec manager is running
        :param args: centec manager args
        """
        daemon = CentecDaemon(CentecTorMechanismDriver.pid_file,
                              CentecTorMechanismDriver.centec_manger_name)
        if daemon.is_running():
            pass
        else:
            LOG.error(_("Centec manager is not running, restarting ..."))
            self.run_centec_manager(args)

    def centec_manager_monitor_timer(self, args):
        """
        Thread to check centec manager is running
        :param args: centec manager args
        """
        try:
            # kill manager if any is running
            daemon = CentecDaemon(CentecTorMechanismDriver.pid_file,
                                  CentecTorMechanismDriver.centec_manger_name)
            pid = 0
            if daemon.is_running():
                pid = daemon.read()
                utils.execute(['kill', '-9', pid], CentecTorMechanismDriver.root_helper)
        except Exception as e:
            LOG.error(_("Can't kill centec manager pid: %(pid)s."
                        "Exception: %(exception)s"), {'pid': pid, 'exception': e})

        try:
            monitor_timer = loopingcall.FixedIntervalLoopingCall(self._centec_manager_monitor, args)
            # check manager running for every 10 seconds
            monitor_timer.start(interval=CentecTorMechanismDriver.monitor_interval)
        except Exception as e:
            LOG.error(_("Centec manager monitor thread can't start."
                        "Exception: %(exception)s"), {'exception': e})

    def initialize(self):
        """
        Initialization
        """
        if self.manager_auto_start:
            self.centec_manager_monitor_timer(self.centec_manager_args)
        if self.rpc_type == 'json-rpc':
            self.rpc_handler = JsonRpcDriver(self.manager_ip, self.manager_nb_port)
        elif self.rpc_type == 'xmpp':
            self.rpc_handler = XmppDriver(self.manager_ip, self.manager_nb_port)
        else:
            self.rpc_handler = None
        self._setup_rpc()

    def _setup_rpc(self):
        """
        Setup RPC
        """
        self.rpc_context = context.RequestContext('neutron', 'neutron',
                                                  is_admin=False)
        self.conn = n_rpc.create_connection(new=True)
        self.endpoints = [CentecRpcCallbacks(self.rpc_handler)]
        self.conn.create_consumer(CENTEC_RPC_TOPIC, self.endpoints, fanout=False)
        # Consume from all consumers in a thread
        self.conn.consume_in_threads()

    def _get_network_info(self, context):
        """
        Get network information from context
        :param context: network context
        """
        network = {}
        data = {}
        network_id = str(context.get('id', ''))
        data['network_id'] = network_id
        data['network_name'] = str(context.get('name', ''))
        data['network_type'] = str(context.get('provider:network_type', ''))
        if self.manager_vlan_alloc_type == 'network':
            data['segmentation_id'] = context.get('provider:segmentation_id', None)
        data['tenant_id'] = str(context.get('tenant_id', ''))

        context_str = json.dumps(data, sort_keys=True)
        data['md5sum'] = hashlib.md5(context_str).hexdigest()

        data['field_not_in_md5'] = ['md5sum']
        if self.manager_vlan_alloc_type != 'network':
            data['field_not_in_md5'].append('segmentation_id')

        if data['network_id'] == '':
            LOG.error(_('Get creating network information failed'))
            return None
        network[network_id] = data
        return network

    def _get_port_info(self, context):
        """
        Get port information from context
        :param context: port context
        """
        port = {}
        data = dict()
        old_host_name = ''

        if context.original is not None:
            old_host_name = context.original.get('binding:host_id', '')

        context = context._port
        port_id = str(context.get('id', ''))
        data['device_owner'] = str(context.get('device_owner', ''))
        # don't create port "network:floating_ip
        if data['device_owner'] == "network:floatingip":
            return None
        data['host_name'] = str(context.get('binding:host_id', ''))
        if len(context.get('fixed_ips', [])) > 0:
            data['subnet_id'] = str(context['fixed_ips'][0].get('subnet_id', ''))
            data['ip_address'] = str(context['fixed_ips'][0].get('ip_address', ''))
        data['device_id'] = str(context.get('device_id', ''))
        data['mac'] = str(context.get('mac_address', ''))
        data['network_id'] = str(context.get('network_id', ''))
        data['admin_state_up'] = context.get('admin_state_up', '')
        data['port_id'] = port_id
        data['tenant_id'] = str(context.get('tenant_id', ''))

        context_str = json.dumps(data, sort_keys=True)
        data['md5sum'] = hashlib.md5(context_str).hexdigest()

        data['field_not_in_md5'] = ['md5sum']
        data['field_not_in_md5'].append('old_host_name')
        data['old_host_name'] = old_host_name

        if data['port_id'] == '':
            LOG.error(_('Get creating port information failed'))
            return None

        if port_id != '':
            port[port_id] = data
        return port

    def _get_subnet_info(self, context):
        """
        Get subnet information from context
        :param context: subnet context
        """

        subnet = {}
        data = {}
        subnet_id = str(context.get('id', ''))
        data['subnet_id'] = subnet_id
        data['subnet_name'] = str(context.get('name', ''))
        data['tenant_id'] = str(context.get('tenant_id', ''))
        data['network_id'] = str(context.get('network_id', ''))
        data['ip_version'] = str(context.get('ip_version', ''))
        data['gateway_ip'] = str(context.get('gateway_ip', ''))
        ip_mask = str(context.get('cidr', ''))
        data['enable_dhcp'] = context.get('enable_dhcp', '')
        data['shared'] = context.get('shared', '')
        if subnet_id == '':
            LOG.error(_('Get creating subnet information failed'))
            return None
        data['network'], data['network_mask'] = ip_mask.split('/')

        context_str = json.dumps(data, sort_keys=True)
        data['md5sum'] = hashlib.md5(context_str).hexdigest()

        data['field_not_in_md5'] = ['md5sum']

        if subnet_id != '':
            subnet[subnet_id] = data
        return subnet

#     def create_network_precommit(self, context):
#         """
#         Create network precommit
#         @todo: not implemented
#         :param context: network context
#         """
#         pass

    def create_network_postcommit(self, context):
        """
        Create network, by calling TOR agent RPC
        :param context: network context
        """
        if self.rpc_handler is None:
            return
        network = self._get_network_info(context._network)
        for _, _network in network.items():
            network_type = _network.get('network_type', '')
            if network_type not in CentecConstant.SUPPORTED_NETWORK_TYPES and len(CentecConstant.SUPPORTED_NETWORK_TYPES) > 0:
                return
        if network is not None:
            try:
                self.rpc_handler.create_network(network)
            except:
                pass

#     def update_network_precommit(self, context):
#         """
#         Update network precommit
#         @todo: not implemented
#         :param context: network context
#         """
#         pass

    def update_network_postcommit(self, context):
        """
        Update network, by calling TOR agent RPC
        :param context: network context
        """
        if self.rpc_handler is None:
            return
        network = self._get_network_info(context._network)
        for _, _network in network.items():
            network_type = _network.get('network_type', '')
            if network_type not in CentecConstant.SUPPORTED_NETWORK_TYPES and len(CentecConstant.SUPPORTED_NETWORK_TYPES) > 0:
                return
        if network is not None:
            try:
                self.rpc_handler.update_network(network)
            except:
                pass

#     def delete_network_precommit(self, context):
#         """
#         Delete network precommit
#         @todo: not implemented
#         :param context: network context
#         """
#         pass

    def delete_network_postcommit(self, context):
        """
        Delete network, by calling TOR agent RPC
        :param context: network context
        """
        if self.rpc_handler is None:
            return
        network = self._get_network_info(context._network)
        for _, _network in network.items():
            network_type = _network.get('network_type', '')
            if network_type not in CentecConstant.SUPPORTED_NETWORK_TYPES and len(CentecConstant.SUPPORTED_NETWORK_TYPES) > 0:
                return
        if network is not None:
            try:
                self.rpc_handler.delete_network(network)
            except:
                pass

#     def create_port_precommit(self, context):
#         """@todo Centec create_port_precommit."""
#         return

    def create_port_postcommit(self, context):
        """
        Create port, by calling TOR agent RPC
        :param context: port context
        """
        if self.rpc_handler is None:
            return
        port = self._get_port_info(context)
        if port is not None:
            try:
                self.rpc_handler.create_port(port)
            except:
                pass

#     def update_port_precommit(self, context):
#         """@todo Centec update_port_precommit."""
#         return

    def update_port_postcommit(self, context):
        """
        Update port, by calling TOR agent RPC
        :param context: port context
        """
        if self.rpc_handler is None:
            return
        port = self._get_port_info(context)
        if port is not None:
            try:
                self.rpc_handler.update_port(port)
            except:
                pass

#     def delete_port_precommit(self, context):
#         """Delete information about a VM and host from the DB."""
#         return

    def delete_port_postcommit(self, context):
        """
        Delete port, by calling TOR agent RPC
        :param context: port context
        """
        if self.rpc_handler is None:
            return
        port = self._get_port_info(context)
        if port is not None:
            try:
                self.rpc_handler.delete_port(port)
            except:
                pass

#     def create_subnet_precommit(self, context):
#         """@todo Centec create_subnet_precommit."""
#         return

    def create_subnet_postcommit(self, context):
        """
        Create subnet, by calling TOR agent RPC
        :param context: subnet context
        """
        if self.rpc_handler is None:
            return
        subnet = self._get_subnet_info(context._subnet)
        if subnet is not None:
            try:
                self.rpc_handler.create_subnet(subnet)
            except:
                pass

#     def update_subnet_precommit(self, context):
#         """@todo Centec update_subnet_precommit."""
#         return

    def update_subnet_postcommit(self, context):
        """
        Update subnet, by calling TOR agent RPC
        :param context: subnet context
        """
        if self.rpc_handler is None:
            return
        subnet = self._get_subnet_info(context._subnet)
        if subnet is not None:
            try:
                self.rpc_handler.update_subnet(subnet)
            except:
                pass

#     def delete_subnet_precommit(self, context):
#         """@todo Centec delete_subnet_precommit."""
#         return

    def delete_subnet_postcommit(self, context):
        """
        Delete subnet, by calling TOR agent RPC
        :param context: subnet context
        """
        if self.rpc_handler is None:
            return
        try:
            self.rpc_handler.delete_subnet({str(context._subnet.get('id', '')): {}})
        except:
            pass

    def check_segment_for_agent(self, segment, agent):
        """
        Check segment for agent
        :param segment: network segment
        :param agent: agent
        """
        mappings = agent['configurations'].get('interface_mappings', {})
        tunnel_types = agent['configurations'].get('tunnel_types', [])
        LOG.debug("Centec mech driver - Checking segment: %(segment)s "
                  "for mappings: %(mappings)s "
                  "with tunnel_types: %(tunnel_types)s",
                  {'segment': segment, 'mappings': mappings,
                   'tunnel_types': tunnel_types})
        network_type = segment[api.NETWORK_TYPE]
        if network_type == 'gre':
            return True
        if network_type == 'local':
            return True
        elif network_type in tunnel_types:
            return True
        elif network_type in 'flat':
            return True
        elif network_type in ['vlan']:
            return segment[api.PHYSICAL_NETWORK] in mappings
        else:
            return False
