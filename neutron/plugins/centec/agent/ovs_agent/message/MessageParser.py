#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent Message parser module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json
import struct

from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST
from neutron.plugins.centec.agent.ovs_agent.lib.Message import Message
from neutron.plugins.centec.agent.ovs_agent.lib.MessageType import MessageType as MsgType


class MessageParser(object):
    def _is_legal_msg(self, msg):
        '''
        parse message type
        :param msg: Message class
        '''
        if not isinstance(msg, Message) and \
           not isinstance(msg.get_data(), dict):
            return False

        # check msg version
        if msg.get_version() != CONST.MSG_VERSION:
            return False
        # check msg type
        if msg.get_type() in MsgType.register_msg:
            return True

        return False

    def handler_msg(self, msg):
        '''
        division different message
        :param msg: Message class
        '''
        legal = self._is_legal_msg(msg)
        if not legal:
            return None

        return msg.get_type()

    def encode_msg(self, msg):
        '''
        encode msg to Message class
        :param msg: data
        '''
        # tanslate json
        json_str = json.dumps(msg.get_data())
        data_buffer = bytearray(json_str.encode("utf-8"))

        # encapsulation message (TLV)
        buf = bytearray(CONST.MSG_HEADER_LENGTH)
        struct.pack_into("!B", buf, 0, msg.get_version())

        struct.pack_into("!B", buf, CONST.MSG_HEADER_VERSION_LENGTH,
                         msg.get_type())

        struct.pack_into("!H", buf, CONST.MSG_HEADER_VERSION_LENGTH +
                         CONST.MSG_HEADER_TYPE_LENGTH, msg.get_xid())

        struct.pack_into("!I", buf, CONST.MSG_HEADER_VERSION_LENGTH +
                         CONST.MSG_HEADER_TYPE_LENGTH +
                         CONST.MSG_HEADER_XID_LENGTH,
                         CONST.MSG_HEADER_LENGTH + len(data_buffer))
        buf += data_buffer

        return buf

    def decode_msg(self, version, msg_type, xid, msg_data):
        '''
        when recv from outer, first parse head to encapsulation Message class
        :param version: negotiate version
        :param msg_type: message type
        :param xid: send message xid
        :param msg_data: json
        '''
        # tanslate from json
        msg_str = msg_data.decode("utf-8")

        json_data = json.loads(msg_str)
        if not isinstance(json_data, dict):
            raise

        return Message(version, msg_type, xid, json_data)
