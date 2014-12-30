#!/usr/bin/env python
# Copyright 2014 Centec, Inc.
# All Rights Reserved.
#

import sys
import time
import traceback

import eventlet
import ovs_config
from oslo.config import cfg
from neutron.agent.linux import ovs_lib
from neutron.agent.linux import polling
from neutron.common import config as common_config
from neutron.agent import rpc as agent_rpc
from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron import context
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from neutron.openstack.common import loopingcall
from neutron.plugins.centec.agent.ovs_agent.ovs_bridge_agent.Agent import Agent
from neutron.agent import securitygroups_rpc as sg_rpc
from neutron.plugins.centec.agent.ovs_agent.lib import hub
from neutron.plugins.centec.agent.ovs_agent.lib.hub import Queue
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


class PluginApi(agent_rpc.PluginApi,
                sg_rpc.SecurityGroupServerRpcApiMixin):
    pass


class SecurityGroupAgent(sg_rpc.SecurityGroupAgentRpcMixin):
    def __init__(self, context, plugin_rpc, root_helper):
        self.context = context
        self.plugin_rpc = plugin_rpc
        self.root_helper = root_helper
        self.init_firewall(defer_refresh_firewall=True)


class NeutronAgent(n_rpc.RpcCallback,
                   sg_rpc.SecurityGroupAgentRpcCallbackMixin):
    RPC_API_VERSION = '1.1'

    def __init__(self, queue, int_br, log):
        super(NeutronAgent, self).__init__()
        self._agent_state = {
            'binary': 'centec-openvswitch-agent',
            'host': cfg.CONF.host,
            'topic': "DVR",
            'configurations': {},
            'agent_type': "Dvr vSwitch agent",
            'start_flag': True
        }

        self._log = log
        self._polling_q = queue
        self._int_br = int_br
        self._updated_ports = set()

        # setup_rpc
        self._agent_id = 'dvr-agent-%s' % cfg.CONF.host
        self._plugin_rpc = PluginApi(topics.PLUGIN)
        self._state_rpc = agent_rpc.PluginReportStateAPI(topics.PLUGIN)
        # Handle updates from service
        self._endpoints = [self]
        # RPC network init
        self._context = context.get_admin_context_without_session()
        # Define the listening consumers for the agent
        self._consumers = [[topics.SECURITY_GROUP, topics.UPDATE],
                           [topics.PORT, topics.UPDATE]]
        self._connection = agent_rpc.create_consumers(self._endpoints,
                                                      topics.AGENT,
                                                      self._consumers)
        # Security group agent support
        self.sg_agent = SecurityGroupAgent(self._context,
                                           self._plugin_rpc,
                                           cfg.CONF.AGENT.root_helper)

        self._polling_interval = cfg.CONF.AGENT.polling_interval
        self._minimize_polling = cfg.CONF.AGENT.minimize_polling

    def _agent_has_updates(self, polling_manager):
        return (polling_manager.is_polling_required or
                self._updated_ports or
                self.sg_agent.firewall_refresh_needed())

    def port_update(self, context, **kwargs):
        port = kwargs.get('port')
        # Put the port identifier in the updated_ports set.
        # Even if full port details might be provided to this call,
        # they are not used since there is no guarantee the notifications
        # are processed in the same order as the relevant API requests
        self._updated_ports.add(port['id'])
        self._log.debug("port_update message processed for port %s" % port['id'])

    def process_network_ports(self):
        cur_ports = set()
        with polling.get_polling_manager(self._minimize_polling,
                                         cfg.CONF.AGENT.root_helper,
                                         CONST.DEFAULT_OVSDBMON_RESPAWN) as pm:
            pm.force_polling()
            while True:
                start = time.time()
                if self._agent_has_updates(pm):
                    self._log.debug("is polling..!")
                    tmp_ports = self._int_br.get_vif_port_set()
                    del_ports = cur_ports - tmp_ports
                    add_ports = tmp_ports - cur_ports
                    cur_ports = tmp_ports
                    update_ports = self._updated_ports
                    self._updated_ports = set()

                    devices_added_updated = add_ports | update_ports
                    if devices_added_updated:
                        self.sg_agent.setup_port_filters(add_ports, update_ports)
                        for port_id in add_ports:
                            try:
                                details = \
                                    self._plugin_rpc.get_device_details(self._context,
                                                                        port_id,
                                                                        self._agent_id)
                            except:
                                self._log.error("Port:%s Get details error" % port_id)
                                continue

                            if "port_id" in details:
                                if details.get("admin_state_up"):
                                    self._plugin_rpc.update_device_up(self._context,
                                                                      port_id,
                                                                      self._agent_id,
                                                                      cfg.CONF.host)
                                else:
                                    self._plugin_rpc.update_device_down(self._context,
                                                                        port_id,
                                                                        self._agent_id,
                                                                        cfg.CONF.host)
                                self._polling_q.put({port_id: "ADD"})

                    if del_ports:
                        self.sg_agent.remove_devices_filter(del_ports)
                        for port_id in del_ports:
                            self._plugin_rpc.update_device_down(self._context,
                                                                port_id,
                                                                self._agent_id,
                                                                cfg.CONF.host)
                            self._polling_q.put({port_id: "DEL"})

                    if not add_ports and not del_ports:
                        self._log.debug("polling null..!")
                        self.sg_agent.setup_port_filters(set(), set())

                    pm.polling_completed()

                # sleep till end of polling interval
                elapsed = (time.time() - start)
                if (elapsed < self._polling_interval):
                    time.sleep(self._polling_interval - elapsed)

    def register_to_neutron(self):
        report_interval = cfg.CONF.AGENT.report_interval
        if report_interval:
            heartbeat = loopingcall.FixedIntervalLoopingCall(self._report_state)
            heartbeat.start(interval=report_interval)

    def _report_state(self):
        # How many devices are likely used by a VM
        self._agent_state.get('configurations')['devices'] = 1
        try:
            self._state_rpc.report_state(self._context, self._agent_state)
            self._agent_state.pop('start_flag', None)
            self._log.debug("report state to neutron..!")
        except:
            self._log.error(traceback.format_exc())


def daemon_loop(queue, int_br, log):
    rpc = NeutronAgent(queue, int_br, log)
    rpc.register_to_neutron()
    try:
        rpc.process_network_ports()
    except:
        log.info(traceback.format_exc())


def main():
    eventlet.monkey_patch()
    cfg.CONF(project='neutron')
    common_config.init(sys.argv[1:])
    common_config.setup_logging()

    LOG = Logger("ovs_agent.agent")

    try:
        integ_br = cfg.CONF.AGENT.integration_bridge
        flat_net_br = cfg.CONF.AGENT.flat_bridge
        root_helper = cfg.CONF.AGENT.root_helper

        int_br = ovs_lib.OVSBridge(integ_br, root_helper)
        int_br.create()
        int_br.set_secure_mode()
        int_br.set_protocols("OpenFlow10,OpenFlow13")
        int_br.delete_port("flat_patch")

        if "dummy" != cfg.CONF.AGENT.lldp_interface:
            # create and get physical port's ofport
            lldp_ofport = int_br.add_port(cfg.CONF.AGENT.lldp_interface)
            int_br.remove_all_flows()
        else:
            lldp_ofport = None

        if "dummy" != cfg.CONF.AGENT.flat_interface:
            flat_br = ovs_lib.OVSBridge(flat_net_br, root_helper)
            flat_br.create()
            flat_br.set_secure_mode()
            flat_br.set_protocols("OpenFlow10,OpenFlow13")
            flat_br.delete_port("int_patch")

            # create and get physical port's ofport
            flat_br.add_port(cfg.CONF.AGENT.flat_interface)
            flat_br.remove_all_flows()
            flat_br.add_flow(priority=1, actions="normal")

            patch_int_ofport = int_br.add_patch_port("flat_patch", "int_patch")
            patch_flat_ofport = flat_br.add_patch_port("int_patch", "flat_patch")

            int_br.set_db_attribute("Port", "flat_patch",
                                    "tag", CONST.DEFAULT_VLAN)
            int_br.set_db_attribute("Interface", "flat_patch",
                                    "options:peer", "int_patch")

            int_br.add_flow(in_port=patch_int_ofport,
                            priority=CONST.UNITCAST_PRO,
                            actions="normal")

            flat_br.set_db_attribute("Interface", "int_patch",
                                     "options:peer", "flat_patch")

    except:
        LOG.error("Init ovs bridge fail..!")
        LOG.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if not lldp_ofport:
            LOG.error("Get physical output fail..!")
            sys.exit(1)

    polling_q = Queue(1024)
    hub.spawn(daemon_loop, polling_q, int_br, LOG)

    PLUGIN_IP = cfg.CONF.AGENT.cloud_manager_ip
    PLUGIN_PORT = cfg.CONF.AGENT.connect_port

    try:
        ovs_bridge_agent = Agent(int_br, lldp_ofport, polling_q,
                                 PLUGIN_IP, PLUGIN_PORT)
        # startup Agent
        ovs_bridge_agent.startup()
    except:
        sys.exit(1)
