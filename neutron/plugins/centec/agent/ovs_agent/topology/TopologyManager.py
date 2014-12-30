#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent topo module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import socket
import traceback

from neutron.plugins.centec.agent.ovs_agent.lib import hub
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from neutron.plugins.centec.agent.ovs_agent.flow.FlowManager import FlowManager


class TopologyManager(object):
    def __init__(self, db, polling_q, int_br, ofport, lock):
        '''
        init
        :param db: database
        :param int_br: ovs-bridge
        '''
        self._db = db
        self._host_name = socket.gethostname()
        self._log = Logger("ovs_agent.topo")
        self._int_br = int_br
        self._flow_manager = FlowManager(self._db, self._host_name,
                                         int_br, ofport)
        self._polling_q = polling_q
        self._lock = lock
        self._wait_port = {}
        self._auxiliary_db = {}
        self._topo_th = hub.spawn(self._topo_start)
        # seconds
        self._keep_alive_interval = CONST.TOPO_SLEEP_INTERVAL

    def _topo_start(self):
        while True:
            if self._lock.get_sync_lock():
                hub.sleep(self._keep_alive_interval)
                continue
            try:
                self._calculate_topo()
            except:
                self._log.info(traceback.format_exc())

    def _calculate_topo(self):
        '''
        topo calculate
        '''
        # check tenant state whether changed
        tenants = self._calculate_tenant()
        if not tenants:
            hub.sleep(self._keep_alive_interval)
            return

        # check host whether connect to tor
        (state, db_msg) = self._db.lookup_entry_from_db(CONST.DBTABLE_HOST,
                                                        self._host_name)
        if not state:
            self._log.warn("Agent lose contact with tor..!")
            return True

        for tenant_id in tenants:
            # if this tenant has not networks, no need to calculate
            networks = self._calculate_networks(tenant_id)
            if not networks:
                continue

            # how many subnet exist in local/remote host
            local_subnets = {}
            remote_subnets = {}

            for network_id in networks:
                # if this network has not subnets, no need to calculate
                is_flat_net, subnets = self._calculate_subnets(network_id)
                if not subnets:
                    continue

                for subnet_id in subnets:
                    # if this subnet has not ports, no need to calculate
                    self._log.debug("subnet_id:%s" % subnet_id)
                    ports = self._calculate_ports(subnet_id)
                    if not ports:
                        continue

                    # calculate this subnet's port in local/remote host
                    (local_ports, remote_ports) = \
                        self._classify_ports_per_host(tenant_id, ports)

                    self._log.debug("Local ports:%s" % local_ports)
                    self._log.debug("remote ports:%s" % remote_ports)

                    if is_flat_net:
                        # calculate normal flows
                        self._flow_manager.calculate_normal_flows(local_ports,
                                                                  remote_ports)
                        continue

                    # calculate identify flows
                    self._flow_manager.calculate_identify_flows(subnet_id,
                                                                local_ports,
                                                                remote_ports)
                    # calculate broadcast flows
                    self._flow_manager.calculate_broadcast_flows(subnet_id,
                                                                 local_ports,
                                                                 remote_ports)
                    # calculate forwarding flows
                    self._flow_manager.calculate_forwarding_flows(subnet_id,
                                                                  local_ports,
                                                                  remote_ports)

                    if 0 != len(local_ports[tenant_id]):
                        local_subnets[subnet_id] = local_ports[tenant_id]

                    if 0 != len(remote_ports[tenant_id]):
                        remote_subnets[subnet_id] = remote_ports[tenant_id]

            # calculate route flows
            self._flow_manager.calculate_route_flows(tenant_id, local_subnets,
                                                     remote_subnets)
            # add this tenant's flows to ovs
            self._flow_manager.add_flows_to_ovs(tenant_id)

        return True

    def _calculate_tenant(self):
        '''
        tenant calculate
        '''
        tenants = set()
        self._lock.set_topo_lock(True)

        while True:
            if self._polling_q.empty():
                if 0 != len(self._wait_port):
                    del_ports = set()
                    for port_id in self._wait_port:
                        if 10 < self._wait_port[port_id]:
                            del_ports.add(port_id)
                            continue

                        state, port_info = \
                            self._db.lookup_entry_from_db(CONST.DBTABLE_PORT,
                                                          port_id)
                        if state:
                            del_ports.add(port_id)
                            if CONST.IF_GW == port_info.get_device_owner() or \
                               CONST.IF_FLOAT == port_info.get_device_owner():
                                continue

                            tenants.add(port_info.get_tenant_id())
                            self._auxiliary_db[port_id] = port_info.get_tenant_id()
                        else:
                            if port_id not in self._wait_port:
                                self._wait_port[port_id] = 1
                            else:
                                self._wait_port[port_id] += 1

                    if 0 != len(del_ports):
                        for port_id in del_ports:
                            self._wait_port.pop(port_id)
                break
            else:
                port_dict = self._polling_q.get()
                for port_id in port_dict:
                    if "ADD" == port_dict[port_id]:
                        state, port_info = self._db.lookup_entry_from_db(CONST.DBTABLE_PORT,
                                                                         port_id)
                        if state:
                            if CONST.IF_GW == port_info.get_device_owner() or \
                               CONST.IF_FLOAT == port_info.get_device_owner():
                                continue

                            tenants.add(port_info.get_tenant_id())
                            self._auxiliary_db[port_id] = port_info.get_tenant_id()
                        else:
                            if port_id not in self._wait_port:
                                self._wait_port[port_id] = 1
                            else:
                                self._wait_port[port_id] += 1
                            self._log.warn("Port:%s recv from polling queue not found in database"
                                           % port_id)
                    elif "DEL" == port_dict[port_id]:
                        state, port_info = self._db.lookup_entry_from_db(CONST.DBTABLE_PORT,
                                                                         port_id)
                        if state:
                            if CONST.IF_GW == port_info.get_device_owner() or \
                               CONST.IF_FLOAT == port_info.get_device_owner():
                                continue

                            tenants.add(port_info.get_tenant_id())
                        else:
                            if port_id in self._auxiliary_db:
                                tenants.add(self._auxiliary_db[port_id])
                                self._auxiliary_db.pop(port_id)

        if 0 != len(self._db.is_vlan_changed()):
            for tenant_id in self._db.is_vlan_changed():
                tenants.add(tenant_id)
            self._db.is_vlan_changed().clear()

        if 0 == len(tenants):
            self._lock.set_topo_lock(False)
            return None

        return tenants

    def _calculate_networks(self, tenant_id):
        '''
        network calculate
        :param tenant_id: tenant id
        '''
        state, tenant_info = self._db.lookup_entry_from_db(CONST.DBTABLE_TENANT,
                                                           tenant_id)
        if not state:
            return None

        if 0 == len(tenant_info.get_networks()):
            return None

        return tenant_info.get_networks()

    def _calculate_subnets(self, network_id):
        '''
        subnet calculate
        :param network_id: network id
        '''
        is_flat_net = False
        subnets = None

        state, network_info = self._db.lookup_entry_from_db(CONST.DBTABLE_NETWORK,
                                                            network_id)
        if state:
            if 0 != len(network_info.get_subnets()):
                subnets = network_info.get_subnets()
            if "flat" == network_info.get_network_type():
                is_flat_net = True

        return (is_flat_net, subnets)

    def _calculate_ports(self, subnet_id):
        '''
        port calculate
        :param subnet_id: subnet id
        '''
        state, subnet_info = self._db.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                           subnet_id)
        if not state:
            return None

        if 0 == len(subnet_info.get_ports()):
            return None

        return subnet_info.get_ports()

    def _classify_ports_per_host(self, tenant_id, ports):
        '''
        division ports per host
        :param tenant_id: tenant id
        :param ports: ports set()
        '''
        local_ports = {}
        local_ports[tenant_id] = set()
        remote_ports = {}
        remote_ports[tenant_id] = set()

        for port_id in ports:
            state, port_info = self._db.lookup_entry_from_db(CONST.DBTABLE_PORT,
                                                             port_id)
            if state:
                if self._host_name == port_info.get_host_name():
                    attrs = self._int_br.get_vif_port_by_id(port_id)
                    if attrs:
                        port_info.set_ofport_id(attrs.ofport)
                        local_ports[tenant_id].add(port_info)
                        self._log.debug("my port:%s get ofport:%s"
                                        % (port_id, attrs.ofport))
                    else:
                        self._log.debug("my port:%s can't find ofport"
                                        % port_id)
                else:
                    remote_ports[tenant_id].add(port_info)

        return (local_ports, remote_ports)
