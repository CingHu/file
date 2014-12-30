#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent main module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import struct
import traceback

from neutron.plugins.centec.agent.ovs_agent.lib import hub
from neutron.plugins.centec.agent.ovs_agent.lib.hub import socket
from neutron.plugins.centec.agent.ovs_agent.lib.hub import Queue
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST
from neutron.plugins.centec.agent.ovs_agent.message.MessageParser import MessageParser
from neutron.plugins.centec.agent.ovs_agent.lib.MessageType import MessageType as MsgType
from neutron.plugins.centec.agent.ovs_agent.sync.Sync import Sync
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from neutron.plugins.centec.agent.ovs_agent.topology.TopologyManager import TopologyManager
from neutron.plugins.centec.agent.ovs_agent.lldp.LldpManager import LldpManager


class Lock(object):
    def __init__(self):
        self._sync_lock = True
        self._topo_lock = False

    def get_sync_lock(self):
        return self._sync_lock

    def set_sync_lock(self, status):
        self._sync_lock = status

    def get_topo_lock(self):
        return self._topo_lock

    def set_topo_lock(self, status):
        self._topo_lock = status


class Agent(object):
    def __init__(self, int_br, ofport, polling_q, address, port):
        '''
        init agent
        :param int_br: ovs-bridge
        :param ofport: physical port's ofport
        :param address: cloud-manager ip address
        :param port: connection port
        '''
        # cloud mananger address
        self._manager = (address, port)
        self._polling_q = polling_q
        self._is_active = False
        self._socket = None
        # seconds
        self._keep_alive_interval = CONST.AGENT_SLEEP_INTERVAL
        # send/recv thread
        self._rx_th = None
        self._tx_th = None
        # send/recv queue
        self._send_queue = None
        self._recv_queue = None
        # module
        self._msg_parser = None
        self._lock = Lock()
        self._int_br = int_br
        # get physical port's ofport
        self._ofport = ofport
        self._sync = None
        self._topo = None
        self._log = Logger("ovs_agent.agent")

    def _connect(self):
        '''
        connect to cloud manager
        '''
        while True:
            # detect idle time
            if self._is_active:
                hub.sleep(self._keep_alive_interval)
                continue

            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect(self._manager)
            except:
                hub.sleep(self._keep_alive_interval)
                self._log.info("Try to connect manager again..!")
                continue
            else:
                # clear queue if have data
                while True:
                    if not self._send_queue.empty():
                        msg = self._send_queue.get()
                    else:
                        if not self._recv_queue.empty():
                            msg = self._recv_queue.get()
                        else:
                            break

                self._is_active = True
                self._log.info("Connect manager success..!")
                if not self._sync:
                    # handle message sync
                    self._sync = Sync(self._msg_parser,
                                      self._send_queue,
                                      self._recv_queue,
                                      self._polling_q,
                                      self._lock)
                if not self._topo:
                    # handle calculate topo
                    self._topo = TopologyManager(self._sync.get_db(),
                                                 self._polling_q,
                                                 self._int_br,
                                                 self._ofport,
                                                 self._lock)
                # send first request sync message
                self._sync.send_sync_request()

    def _recv_loop(self):
        '''
        recv thread: recv msg from socket
        '''

        required_len = CONST.MSG_HEADER_LENGTH
        buf = bytearray()

        while True:
            if not self._is_active:
                hub.sleep(self._keep_alive_interval)
                continue

            ret = self._socket.recv(required_len)
            if 0 == len(ret):
                self._is_active = False
                self._socket = None
                self._log.warn("Agent lose contact with manager(recv)..!")
                buf = bytearray()
                continue

            buf += ret

            # recv packet maybe slice
            while len(buf) >= required_len:
                data = buffer(buf[:CONST.MSG_HEADER_LENGTH])
                HEAD = CONST.MSG_HEADER_PACK_STR

                try:
                    (version, msg_type, xid, msg_len) = struct.unpack(HEAD, data)
                except:
                    self._log.error(traceback.format_exc())
                    buf = buf[required_len:]
                    break

                required_len = msg_len
                if len(buf) < required_len:
                    break

                # decode msg from manager
                try:
                    data = buf[CONST.MSG_HEADER_LENGTH: required_len]
                    msg = self._msg_parser.decode_msg(version, msg_type,
                                                      xid, data)
                except:
                    self._log.error(traceback.format_exc())
                    buf = buf[required_len:]
                    required_len = CONST.MSG_HEADER_LENGTH
                    break

                # division real-time/backup message
                if msg_type in MsgType.register_msg:
                    self._recv_queue.put(msg)

                buf = buf[required_len:]
                required_len = CONST.MSG_HEADER_LENGTH

    def _send_loop(self):
        '''
        send thread: send msg to socket
        '''

        while True:
            buf = self._send_queue.get()
            try:
                if self._is_active:
                    self._socket.sendall(buf)
            except:
                self._is_active = False
                self._socket = None
                self._log.warn("Agent lose contact with manager(send)..!")
                self._log.error(traceback.format_exc())

    def startup(self):
        # init queue
        self._send_queue = Queue(128)
        self._recv_queue = Queue(1024)

        try:
            if not self._rx_th:
                self._rx_th = hub.spawn(self._recv_loop)
            if not self._tx_th:
                self._tx_th = hub.spawn(self._send_loop)
            # message type parse
            self._msg_parser = MessageParser()
            # lldp send
            self._lldp = LldpManager()

            self._connect()
        except:
            self._log.error("Agent encounter a mistake, exit now..!")
            self._log.debug(traceback.format_exc())
