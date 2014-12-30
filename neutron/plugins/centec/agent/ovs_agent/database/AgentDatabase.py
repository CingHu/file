#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import traceback
import socket

from neutron.plugins.centec.agent.ovs_agent.lib.Database import Database
from neutron.plugins.centec.agent.ovs_agent.lib.hub import Queue
from neutron.plugins.centec.agent.ovs_agent.lib.Message import Message
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST
from neutron.plugins.centec.agent.ovs_agent.database.TenantMessage import TenantMessage
from neutron.plugins.centec.agent.ovs_agent.database.NetworkMessage import NetworkMessage
from neutron.plugins.centec.agent.ovs_agent.database.SubnetMessage import SubnetMessage
from neutron.plugins.centec.agent.ovs_agent.database.PortMessage import PortMessage
from neutron.plugins.centec.agent.ovs_agent.database.VlanMessage import VlanMessage
from neutron.plugins.centec.agent.ovs_agent.database.HostMessage import HostMessage
from neutron.plugins.centec.agent.ovs_agent.lib.MessageType import MessageType as MsgType


class AgentDatabase(Database):
    def __init__(self, polling_q):
        '''
        init table name in db
        '''
        super(AgentDatabase, self).__init__([CONST.DBTABLE_TENANT,
                                             CONST.DBTABLE_NETWORK,
                                             CONST.DBTABLE_SUBNET,
                                             CONST.DBTABLE_PORT,
                                             CONST.DBTABLE_VLAN,
                                             CONST.DBTABLE_HOST])
        # handle unsequence message
        self._lostfound_q = Queue(128)
        self._timeout = CONST.DB_TIMEOUT
        self._sleep_interval = CONST.DB_SLEEP_INTERVAL
        # assign router/broadcast id
        self._routers = {}
        self._broadcasts = {}
        self._rid = 1
        self._bid = 1
        self._gc = {}
        self._gc["B_ID"] = []
        self._gc["R_ID"] = []
        self._vlan_change = set()
        self._polling_q = polling_q
        self._host_name = socket.gethostname()

    # db op
    def is_vlan_changed(self):
        return self._vlan_change

    def handle_network_entry(self, msg_type, data):
        '''
        handle network message
        :param msg_type: message type
        :param data: Message Class
        '''
        try:
            if msg_type == MsgType.MSG_CREATE_NETWORK or \
               msg_type == MsgType.MSG_UPDATE_NETWORK:
                return self._add_network_entry_to_db(data)
            elif msg_type == MsgType.MSG_DELETE_NETWORK:
                # fix bug: aging handle 2014-12-13
                if isinstance(data, Message):
                    for network_id in data.get_data():
                        return self._del_network_entry_to_db(network_id)
                else:
                    return self._del_network_entry_to_db(data)
            else:
                self._log.error("Can't identify network msg type:%s" % msg_type)
        except:
            self._log.error("Handle network entry error..!")
            self._log.debug(traceback.format_exc())

        return False

    def handle_subnet_entry(self, msg_type, data):
        '''
        handle subnet message
        :param msg_type: message type
        :param data: Message Class
        '''
        try:
            if msg_type == MsgType.MSG_CREATE_SUBNET or \
               msg_type == MsgType.MSG_UPDATE_SUBNET:
                return self._add_subnet_entry_to_db(data)
            elif msg_type == MsgType.MSG_DELETE_SUBNET:
                # fix bug: aging handle 2014-12-13
                if isinstance(data, Message):
                    for subnet_id in data.get_data():
                        return self._del_subnet_entry_to_db(subnet_id)
                else:
                    return self._del_subnet_entry_to_db(data)
            else:
                self._log.error("Can't identify subnet msg type:%s" % msg_type)
        except:
            self._log.error("Handle subnet entry error..!")
            self._log.debug(traceback.format_exc())

        return False

    def handle_port_entry(self, msg_type, data):
        '''
        handle port message
        :param msg_type: message type
        :param data: Message Class
        '''
        try:
            if msg_type == MsgType.MSG_CREATE_PORT or \
               msg_type == MsgType.MSG_UPDATE_PORT:
                return self._add_port_entry_to_db(data)
            elif msg_type == MsgType.MSG_DELETE_PORT:
                # fix bug: aging handle 2014-12-13
                if isinstance(data, Message):
                    for port_id in data.get_data():
                        return self._del_port_entry_to_db(port_id)
                else:
                    return self._del_port_entry_to_db(data)
            else:
                self._log.error("Can't identify port msg type:%s" % msg_type)
        except:
            self._log.error("Handle port entry error..!")
            self._log.debug(traceback.format_exc())

        return False

    def handle_vlan_entry(self, msg_type, data):
        '''
        handle vlan message
        :param msg_type: message type
        :param data: Message Class
        '''
        try:
            if msg_type == MsgType.MSG_CREATE_VLAN or \
               msg_type == MsgType.MSG_UPDATE_VLAN:
                return self._add_vlan_entry_to_db(data)
            elif msg_type == MsgType.MSG_DELETE_VLAN:
                # fix bug: aging handle 2014-12-13
                if isinstance(data, Message):
                    for key in data.get_data():
                        return self._del_vlan_entry_to_db(key)
                else:
                    return self._del_vlan_entry_to_db(data)
            else:
                self._log.error("Can't identify vlan msg type:%s" % msg_type)
        except:
            self._log.error("Handle vlan entry error..!")
            self._log.debug(traceback.format_exc())

        return False

    def handle_link_entry(self, msg_type, data):
        '''
        handle host message
        :param msg_type: message type
        :param data: Message Class
        '''
        try:
            if msg_type == MsgType.MSG_UPDATE_LINK or \
               msg_type == MsgType.MSG_REPLY_LINK:
                return self._update_link_entry_to_db(data)
            else:
                self._log.error("Can't identify host msg type:%s" % msg_type)
        except:
            self._log.error("Handle host entry error..!")
            self._log.debug(traceback.format_exc())

        return False

    # interior implement
    def _add_network_entry_to_db(self, msg):
        '''
        add/update network entry
        :param msg: Message Class
        '''
        data_all = msg.get_data()
        for key, data in data_all.items():
            network_msg = NetworkMessage(data)
            tenant_id = network_msg.get_tenant_id()

            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_NETWORK, key)
            if state:
                # if added before
                self._log.debug("Network:%s updated to database" % key)
                self.update_entry_to_db(CONST.DBTABLE_NETWORK, key, network_msg)
                continue

            self.add_entry_to_db(CONST.DBTABLE_NETWORK, key, network_msg)
            self._log.debug("Network:%s added to database" % key)

            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_TENANT, tenant_id)
            if state:
                # if added before
                tenant_msg = db_msg
            else:
                tenant_msg = TenantMessage(data)
                self.add_entry_to_db(CONST.DBTABLE_TENANT, tenant_id, tenant_msg)
                self._log.debug("Tenant:%s added to database" % tenant_id)

            tenant_msg.set_network(key)
            self._log.debug("Tenant:%s add network:%s" % (tenant_id, key))

        return True

    def _del_network_entry_to_db(self, network_id):
        '''
        del network entry
        :param network_id: network id
        '''
        (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_NETWORK, network_id)
        if state:
            tenant_id = db_msg.get_tenant_id()
            (sub_state, sub_db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_TENANT,
                                                                tenant_id)
            if sub_state:
                # del network from TENANT
                sub_db_msg.get_networks().discard(network_id)
                self._log.debug("Tenant:%s del %s" % (tenant_id, network_id))
            else:
                self._log.warn("Network:%s delete but can't find tenant" % network_id)

            subnets = db_msg.get_subnets().copy()
            if 0 != len(subnets):
                # del network's subnets
                for subnet_id in subnets:
                    self._del_subnet_entry_to_db(subnet_id)

            self.del_entry_from_db(CONST.DBTABLE_NETWORK, network_id)
            self._log.debug("Network:%s deleted to database" % network_id)
        else:
            self._log.warn("Network:%s not in database" % network_id)

        return True

    def _add_subnet_entry_to_db(self, msg):
        '''
        add/update subnet entry
        :param msg: Message Class
        '''
        data_all = msg.get_data()
        for key, data in data_all.items():
            subnet_msg = SubnetMessage(data)
            network_id = subnet_msg.get_network_id()

            (status, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_NETWORK, network_id)
            if status:
                # subnet id added to network
                db_msg.set_subnet(key)
                self._log.debug("Network:%s add to subnet:%s" % (network_id, key))
            else:
                self._log.warn("Subnet msg arrived early:%s" % key)
                self._lostfound_q.put(msg)
                continue

            # set broadcast id
            if key not in self._broadcasts:
                if 0 != len(self._gc["B_ID"]):
                    self._broadcasts[key] = self._gc["B_ID"][0]
                    broadcast_id = self._gc["B_ID"][0]
                    self._gc["B_ID"] = self._gc["B_ID"][1:]
                else:
                    self._broadcasts[key] = self._bid
                    broadcast_id = self._bid
                    self._bid += 1
            else:
                broadcast_id = self._broadcasts[key]

            subnet_msg.set_broadcast_id(broadcast_id)
            self._log.debug("Subnet:%s assign bc_id:%d" % (key, broadcast_id))

            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_SUBNET, key)
            if state:
                # if added before
                self._log.debug("Subnet:%s updated to database" % key)
                self.update_entry_to_db(CONST.DBTABLE_SUBNET, key, subnet_msg)
            else:
                self.add_entry_to_db(CONST.DBTABLE_SUBNET, key, subnet_msg)
                self._log.debug("Subnet:%s added to database" % key)

        return True

    def _del_subnet_entry_to_db(self, subnet_id):
        '''
        del subnet entry
        :param subnet_id: subnet id
        '''
        (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_SUBNET, subnet_id)
        if state:
            network_id = db_msg.get_network_id()
            (sub_state, sub_db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_NETWORK,
                                                                network_id)
            if sub_state:
                # del subnet from NETWORK
                sub_db_msg.get_subnets().discard(subnet_id)
                self._log.debug("Network:%s del %s" % (network_id, subnet_id))
            else:
                self._log.warn("Subte:%s delete but can't find network" % subnet_id)

            ports = db_msg.get_ports().copy()
            if 0 != len(ports):
                # del subnet's port
                for port in ports:
                    self._del_port_entry_to_db(port)

            self.del_entry_from_db(CONST.DBTABLE_SUBNET, subnet_id)
            self._log.debug("Subnet:%s deleted to database" % subnet_id)

            # del broadcast id
            if subnet_id in self._broadcasts:
                free_id = self._broadcasts[subnet_id]
                self._broadcasts.pop(subnet_id)
                self._gc["B_ID"].append(free_id)
                self._log.debug("Subnet set free bc_id:%d" % free_id)
        else:
            self._log.warn("Subnet:%s not in database" % subnet_id)

        return True

    def _add_port_entry_to_db(self, msg):
        '''
        add/update port entry
        :param msg: Message Class
        '''
        data_all = msg.get_data()
        for key, data in data_all.items():
            port_msg = PortMessage(data)
            subnet_id = port_msg.get_subnet_id()
            # fix bug: optimize handle lostfound 2014-12-12
            if not subnet_id:
                continue

            if port_msg.get_device_owner() == CONST.IF_GW:
                continue
            if port_msg.get_device_owner() == CONST.IF_FLOAT:
                continue

            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_SUBNET, subnet_id)
            if state:
                # add to subnet
                db_msg.set_port(key)
                self._log.debug("Port:%s add to Subnet:%s" % (key, subnet_id))

                if port_msg.get_device_owner() == CONST.IF_ROUTER:
                    router_id = port_msg.get_device_id()
                    if router_id not in self._routers:
                        self._routers[router_id] = {}
                        if 0 != len(self._gc["R_ID"]):
                            self._routers[router_id]["id"] = self._gc["R_ID"][0]
                            metadata_id = self._gc["R_ID"][0]
                            self._gc["R_ID"] = self._gc["R_ID"][1:]
                        else:
                            self._routers[router_id]["id"] = self._rid
                            metadata_id = self._rid
                            self._rid += 1
                        self._routers[router_id]["member"] = set()
                        self._routers[router_id]["member"].add(subnet_id)
                        self._log.debug("Subnet:%s assign route_id:%d" % (subnet_id, metadata_id))
                    else:
                        metadata_id = self._routers[router_id]["id"]
                        self._routers[router_id]["member"].add(subnet_id)

                    # set subnet gw
                    db_msg.set_gateways(port_msg.get_device_id(),
                                        port_msg.get_ip_addr(),
                                        port_msg.get_mac_addr(),
                                        metadata_id)
                elif port_msg.get_device_owner() == CONST.IF_DHCP:
                    # set subnet dhcp
                    db_msg.set_dhcp_mac(port_msg.get_mac_addr())
                    db_msg.set_dhcp_ip(port_msg.get_ip_addr())
            else:
                self._log.warn("Port msg arrived early: %s" % key)
                self._lostfound_q.put(msg)
                continue

            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_PORT, key)
            if state:
                self._log.debug("Port:%s updated to database" % key)
                self.update_entry_to_db(CONST.DBTABLE_PORT, key, port_msg)

                self._polling_q.put({key: "ADD"})
            else:
                self.add_entry_to_db(CONST.DBTABLE_PORT, key, port_msg)
                self._log.debug("Port:%s added to database" % key)

                if port_msg.get_host_name() != self._host_name:
                    self._polling_q.put({key: "ADD"})

        return True

    def _del_port_entry_to_db(self, port_id):
        '''
        del subnet entry
        :param port_id: port id
        '''
        (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_PORT, port_id)
        if state:
            host_name = db_msg.get_host_name()
            (sub_state, sub_db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                                db_msg.get_subnet_id())
            if sub_state:
                # del from subnet
                sub_db_msg.get_ports().discard(port_id)
                self._log.debug("Port:%s discard from Subnet:%s" %
                                (port_id, db_msg.get_subnet_id()))

                if db_msg.get_device_owner() == CONST.IF_DHCP:
                    # set subnet dhcp None
                    sub_db_msg.set_dhcp_mac(None)
                    sub_db_msg.set_dhcp_ip(None)
                elif db_msg.get_device_owner() == CONST.IF_ROUTER:
                    router_id = db_msg.get_device_id()
                    if router_id in self._routers:
                        mem_set = self._routers[router_id]["member"]
                        mem_set.remove(db_msg.get_subnet_id())
                        if 0 == len(mem_set):
                            free_rid = self._routers[router_id]["id"]
                            self._gc["R_ID"].append(free_rid)
                            self._routers.pop(router_id)
                            self._log.debug("Set free route_id:%d" % free_rid)

                    # set subnet gw None
                    sub_db_msg.del_gateways(db_msg.get_device_id())
            else:
                self._log.warn("Port:%s delete but can't find subnet" % port_id)

            self.del_entry_from_db(CONST.DBTABLE_PORT, port_id)
            self._log.debug("Port:%s deleted to database" % port_id)

            if host_name != self._host_name:
                self._polling_q.put({port_id: "DEL"})
        else:
            self._log.warn("Port:%s not in database" % port_id)

        return True

    def _add_vlan_entry_to_db(self, msg):
        '''
        add/update vlan entry
        :param msg: Message Class
        '''
        data_all = msg.get_data()
        for key, data in data_all.items():
            # key: tor_ip | tenant_id
            vlan_msg = VlanMessage(data)
            tenant_id = key.split("|")[1]

            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_VLAN, key)
            if state:
                self._log.debug("Vlan:%d updated to database" % vlan_msg.get_vlan_id())
                self.update_entry_to_db(CONST.DBTABLE_VLAN, key, vlan_msg)
            else:
                self.add_entry_to_db(CONST.DBTABLE_VLAN, key, vlan_msg)
                self._log.debug("Vlan:%d added to database" % vlan_msg.get_vlan_id())
            self._vlan_change.add(tenant_id)

        return True

    def _del_vlan_entry_to_db(self, key):
        '''
        del vlan entry
        :param key: key
        '''
        # key: tor_ip | tenant_id
        (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_VLAN, key)
        if state:
            self.del_entry_from_db(CONST.DBTABLE_VLAN, key)
            self._log.debug("Vlan:%s deleted to database" % key)
        else:
            self._log.warn("Vlan:%s not in database" % key)

        return True

    def _update_link_entry_to_db(self, msg):
        '''
        update host entry
        :param msg: Message Class
        '''
        data_all = msg.get_data()
        for key, data in data_all.items():
            (state, db_msg) = self.lookup_entry_from_db(CONST.DBTABLE_HOST, key)
            if state:
                for tor_ip in data:
                    if tor_ip == db_msg.get_tor_id():
                        continue
                    host_msg = HostMessage(data)
                    self.update_entry_to_db(CONST.DBTABLE_HOST, key, host_msg)
                    self._log.debug("Host:%s updated to database" % key)
            else:
                host_msg = HostMessage(data)
                self.add_entry_to_db(CONST.DBTABLE_HOST, key, host_msg)
                self._log.debug("Host:%s added to database" % key)

        return True

    def recv_loop(self):
        '''
        recv message from lostfound queue
        '''
        while True:
            try:
                if self._lostfound_q.empty():
                    break

                msg = self._lostfound_q.get()
                # set message color, if red, discard
                if CONST.GREEN == msg.get_color():
                    msg.set_color(CONST.YELLOW)
                elif CONST.YELLOW == msg.get_color():
                    msg.set_color(CONST.RED)
                else:
                    self._log.warn("Discard red msg:%s" % msg.get_data())
                    continue

                msg_type = msg.get_type()
                if msg_type == MsgType.MSG_CREATE_SUBNET:
                    self._add_subnet_entry_to_db(msg)
                elif msg_type == MsgType.MSG_UPDATE_SUBNET:
                    self._add_subnet_entry_to_db(msg)
                elif msg_type == MsgType.MSG_CREATE_PORT:
                    self._add_port_entry_to_db(msg)
                elif msg_type == MsgType.MSG_UPDATE_PORT:
                    self._add_port_entry_to_db(msg)
            except:
                self._log.error("Lostfound queue have a mistake..!")
                self._log.debug(traceback.format_exc())

