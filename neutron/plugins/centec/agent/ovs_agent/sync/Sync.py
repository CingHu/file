#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent sync module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import traceback

from neutron.plugins.centec.agent.ovs_agent.lib import hub
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST
from neutron.plugins.centec.agent.ovs_agent.lib.MessageType import MessageType
from neutron.plugins.centec.agent.ovs_agent.database.AgentDatabase import AgentDatabase
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from neutron.plugins.centec.agent.ovs_agent.lib.Message import Message
from neutron.plugins.centec.agent.ovs_agent.lib.MessageType import MessageType as MsgType


handler_cb = {}


def register_handler_cb(msg_type):
        '''
        decorate for sync module
        :param msg_type: message type
        '''
        def _register_handler_cb(fn):
            handler_cb[msg_type] = fn.__name__
            return fn
        return _register_handler_cb


class Sync(object):
    def __init__(self, msg_parser, send_queue, recv_queue, polling_q, lock):
        '''
        init
        :param msg_parser: MessageParser
        :param send_queue: send queue
        :param recv_queue: recv queue
        :param int_br: ovs-bridge
        :param ofport: physical port's ofport
        '''
        self._send_q = send_queue
        self._recv_q = recv_queue
        # module
        self._agent_db = AgentDatabase(polling_q)
        self._msg_parser = msg_parser
        self._log = Logger("ovs_agent.sync")
        # recv/send thread
        self._rx_th = hub.spawn(self._recv_from_queue)
        self._tx_th = hub.spawn(self._send_request)
        self._lock = lock

        # seconds
        self._keep_alive_interval = CONST.SYNC_SLEEP_INTERVAL

    def get_db(self):
        return self._agent_db

    # real-time message handle
    @register_handler_cb(MessageType.MSG_CREATE_NETWORK)
    def handle_create_network(self, msg):
        self._log.debug("Handle create network:%s" % msg.string())
        if not self._agent_db.handle_network_entry(msg.get_type(), msg):
            self._log.error("Handle create network error")

    @register_handler_cb(MessageType.MSG_DELETE_NETWORK)
    def handle_delete_network(self, msg):
        self._log.debug("Handle delete network:%s" % msg.string())
        if not self._agent_db.handle_network_entry(msg.get_type(), msg):
            self._log.error("Handle delete network error")

    @register_handler_cb(MessageType.MSG_CREATE_SUBNET)
    def handle_create_subnet(self, msg):
        self._log.debug("Handle create subnet:%s" % msg.string())
        if not self._agent_db.handle_subnet_entry(msg.get_type(), msg):
            self._log.error("Handle create subnet error")

    @register_handler_cb(MessageType.MSG_DELETE_SUBNET)
    def handle_delete_subnet(self, msg):
        self._log.debug("Handle delete subnet:%s" % msg.string())
        if not self._agent_db.handle_subnet_entry(msg.get_type(), msg):
            self._log.error("Handle delete subnet error")

    @register_handler_cb(MessageType.MSG_CREATE_PORT)
    def handle_create_port(self, msg):
        self._log.debug("Handle create port:%s" % msg.string())
        if not self._agent_db.handle_port_entry(msg.get_type(), msg):
            self._log.error("Handle create port error")

    @register_handler_cb(MessageType.MSG_DELETE_PORT)
    def handle_delete_port(self, msg):
        self._log.debug("Handle delete port:%s" % msg.string())
        if not self._agent_db.handle_port_entry(msg.get_type(), msg):
            self._log.error("Handle delete port error")

    @register_handler_cb(MessageType.MSG_CREATE_VLAN)
    def handle_create_vlan(self, msg):
        self._log.debug("Handle create vlan:%s" % msg.string())
        if not self._agent_db.handle_vlan_entry(msg.get_type(), msg):
            self._log.error("Handle create vlan error")

    @register_handler_cb(MessageType.MSG_DELETE_VLAN)
    def handle_delete_vlan(self, msg):
        self._log.debug("Handle delete vlan:%s" % msg.string())
        if not self._agent_db.handle_vlan_entry(msg.get_type(), msg):
            self._log.error("Handle delete vlan error")

    @register_handler_cb(MessageType.MSG_UPDATE_LINK)
    def handle_update_link(self, msg):
        self._log.debug("Handle update link:%s" % msg.string())
        if not self._agent_db.handle_link_entry(msg.get_type(), msg):
            self._log.error("Handle link network error")

    # backup message handle
    @register_handler_cb(MessageType.MSG_UPDATE_NETWORK)
    def handle_update_network(self, msg):
        self._log.debug("Handle update network:%s" % msg.string())
        if not self._agent_db.handle_network_entry(msg.get_type(), msg):
            self._log.error("Handle update network error")

    @register_handler_cb(MessageType.MSG_UPDATE_SUBNET)
    def handle_update_subnet(self, msg):
        self._log.debug("Handle update subnet:%s" % msg.string())
        if not self._agent_db.handle_subnet_entry(msg.get_type(), msg):
            self._log.error("Handle update subnet error")

    @register_handler_cb(MessageType.MSG_UPDATE_PORT)
    def handle_update_port(self, msg):
        self._log.debug("Handle update port:%s" % msg.string())
        if not self._agent_db.handle_port_entry(msg.get_type(), msg):
            self._log.error("Handle update port error")

    @register_handler_cb(MessageType.MSG_UPDATE_VLAN)
    def handle_update_vlan(self, msg):
        self._log.debug("Handle update vlan:%s" % msg.string())
        if not self._agent_db.handle_vlan_entry(msg.get_type(), msg):
            self._log.error("Handle update vlan error")

    # reply message handle
    @register_handler_cb(MessageType.MSG_REPLY_NETWORK)
    def handle_reply_network(self, msg):
        self._log.debug("Handle networks reply:%s" % msg.string())
        if 0 == len(msg.get_data()):
            self._agent_db.clear_table_from_db(CONST.DBTABLE_NETWORK)
            return

        is_update = False
        networks = self._agent_db.lookup_table_from_db(CONST.DBTABLE_NETWORK)
        request_networks = {}
        delete_networks = set()
        request_networks["keys"] = []
        if networks:
            # delete redundance data in db
            keys = msg.get_data().keys()
            for network_id in networks:
                if network_id not in keys:
                    delete_networks.add(network_id)

            if 0 != len(delete_networks):
                for network_id in delete_networks:
                    # fix bug: aging handle 2014-12-13
                    self._agent_db.handle_network_entry(MsgType.MSG_DELETE_NETWORK,
                                                        network_id)
            # update data to db
            for network_id, md5sum in msg.get_data().items():
                if network_id in networks:
                    if md5sum["md5sum"] == networks[network_id].get_md5sum():
                        continue
                is_update = True
                request_networks["keys"].append(network_id)
        else:
            for network_id in msg.get_data():
                request_networks["keys"].append(network_id)
            is_update = True

        if is_update:
            self._log.debug("Send networks request:%s" % request_networks)
            self.send_request_networks(request_networks)

    @register_handler_cb(MessageType.MSG_REPLY_SUBNET)
    def handle_reply_subnet(self, msg):
        self._log.debug("Handle subnets reply:%s" % msg.string())
        if 0 == len(msg.get_data()):
            self._agent_db.clear_table_from_db(CONST.DBTABLE_SUBNET)
            return

        is_update = False
        subnets = self._agent_db.lookup_table_from_db(CONST.DBTABLE_SUBNET)
        request_subnets = {}
        delete_subnets = set()
        request_subnets["keys"] = []
        if subnets:
            # delete redundance data in db
            keys = msg.get_data().keys()
            for subnet_id in subnets:
                if subnet_id not in keys:
                    delete_subnets.add(subnet_id)

            if 0 != len(delete_subnets):
                for subnet_id in delete_subnets:
                    # fix bug: aging handle 2014-12-13
                    self._agent_db.handle_subnet_entry(MsgType.MSG_DELETE_SUBNET,
                                                       subnet_id)
            # update data to db
            for subnet_id, md5sum in msg.get_data().items():
                if subnet_id in subnets:
                    if md5sum["md5sum"] == subnets[subnet_id].get_md5sum():
                        continue
                is_update = True
                request_subnets["keys"].append(subnet_id)
        else:
            for subnet_id in msg.get_data():
                request_subnets["keys"].append(subnet_id)
            is_update = True

        if is_update:
            self._log.debug("Send subnets request:%s" % request_subnets)
            self.send_request_subnets(request_subnets)

    @register_handler_cb(MessageType.MSG_REPLY_PORT)
    def handle_reply_port(self, msg):     
        self._log.debug("Handle ports reply:%s" % msg.string())
        if 0 == len(msg.get_data()):
            self._agent_db.clear_table_from_db(CONST.DBTABLE_PORT)
            return

        is_update = False
        ports = self._agent_db.lookup_table_from_db(CONST.DBTABLE_PORT)
        request_ports = {}
        delete_ports = set()
        request_ports["keys"] = []
        if ports:
            # delete redundance data in db
            keys = msg.get_data().keys()
            for port_id in ports:
                if port_id not in keys:
                    delete_ports.add(port_id)

            if 0 != len(delete_ports):
                for port_id in delete_ports:
                    # fix bug: aging handle 2014-12-13
                    self._agent_db.handle_port_entry(MsgType.MSG_DELETE_PORT,
                                                     port_id)
            # update data to db
            for port_id, md5sum in msg.get_data().items():
                if port_id in ports:
                    if md5sum["md5sum"] == ports[port_id].get_md5sum():
                        continue
                is_update = True
                request_ports["keys"].append(port_id)
        else:
            for port_id in msg.get_data():
                request_ports["keys"].append(port_id)
            is_update = True

        if is_update:
            self._log.debug("Send ports request:%s" % request_ports)
            self.send_request_ports(request_ports)

    @register_handler_cb(MessageType.MSG_REPLY_VLAN)
    def handle_reply_vlan(self, msg):
        self._log.debug("Handle vlans reply:%s" % msg.string())       
        if 0 == len(msg.get_data()):
            self._agent_db.clear_table_from_db(CONST.DBTABLE_VLAN)
            return

        is_update = False
        vlans = self._agent_db.lookup_table_from_db(CONST.DBTABLE_VLAN)
        request_vlans = {}
        delete_vlans = set()
        request_vlans["keys"] = []
        if vlans:
            # delete redundance data in db
            keys = msg.get_data().keys()
            for vlan_id in vlans:
                if vlan_id not in keys:
                    delete_vlans.add(vlan_id)

            if 0 != len(delete_vlans):
                for vlan_id in delete_vlans:
                    # fix bug: aging handle 2014-12-13
                    self._agent_db.handle_vlan_entry(MsgType.MSG_DELETE_VLAN,
                                                     vlan_id)
            # update data to db
            for key, md5sum in msg.get_data().items():
                if key in vlans:
                    if md5sum["md5sum"] == vlans[key].get_md5sum():
                        continue
                is_update = True
                request_vlans["keys"].append(key)
        else:
            for key in msg.get_data():
                request_vlans["keys"].append(key)
            is_update = True

        if is_update:
            self._log.debug("Send vlans request:%s" % request_vlans)
            self.send_request_vlans(request_vlans)

    @register_handler_cb(MessageType.MSG_REPLY_LINK)
    def handle_reply_link(self, msg):
        if 0 == len(msg.get_data()):
            self._agent_db.clear_table_from_db(CONST.DBTABLE_HOST)
            return

        self.handle_update_link(msg)

    def send(self, msg):
        '''
        send message to cloud manager
        :param msg: Message class
        '''
        try:
            buf = self._msg_parser.encode_msg(msg)
        except:
            self._log.error(traceback.format_exc())

        if self._send_q:
            self._send_q.put(buf)

    def send_request_networks(self, data=None):
        if data:
            if not isinstance(data, dict):
                self._log.warn("Networks request error")
                return

            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_NETWORK, 0, data)
        else:
            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_NETWORK, 0, {})
        self.send(msg)

    def send_request_subnets(self, data=None):
        if data:
            if not isinstance(data, dict):
                self._log.warn("Subnets request error")
                return

            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_SUBNET, 0, data)
        else:
            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_SUBNET, 0, {})
        self.send(msg)

    def send_request_ports(self, data=None):
        if data:
            if not isinstance(data, dict):
                self._log.warn("Ports request error")
                return

            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_PORT, 0, data)
        else:
            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_PORT, 0, {})
        self.send(msg)

    def send_request_vlans(self, data=None):
        if data:
            if not isinstance(data, dict):
                self._log.warn("Vlans request error")
                return

            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_VLAN, 0, data)
        else:
            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_VLAN, 0, {})
        self.send(msg)

    def send_request_links(self, data=None):
        if data:
            if not isinstance(data, dict):
                self._log.warn("links request error")
                return

            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_LINK, 0, data)
        else:
            msg = Message(CONST.MSG_VERSION, MessageType.MSG_REQUEST_LINK, 0, {})
        self.send(msg)

    def send_sync_request(self):
        self.send_request_vlans()
        self.send_request_links()
        self.send_request_networks()
        self.send_request_subnets()
        self.send_request_ports()
        self._log.debug("Agent send request message..!")

    def _recv_from_queue(self):
        '''
        recv message from real-time/backups queue
        '''
        while True:
            if self._lock.get_topo_lock():
                hub.sleep(self._keep_alive_interval)
                continue

            if self._recv_q.empty():
                self._agent_db.recv_loop()
                self._lock.set_sync_lock(False)
                hub.sleep(self._keep_alive_interval)
            else:
                self._lock.set_sync_lock(True)
                # handle recv message
                msg = self._recv_q.get()
                msg_type = self._msg_parser.handler_msg(msg)
                if msg_type:
                    try:
                        getattr(self, handler_cb.get(msg_type))(msg)
                    except:
                        self._log.debug(traceback.format_exc())

    def _send_request(self):
        '''
        send request message to cloud manager
        '''
        # delay 5s to start timer
        hub.sleep(self._keep_alive_interval * 5)

        while True:
            hub.sleep(self._keep_alive_interval * 60)
            self.send_sync_request()
