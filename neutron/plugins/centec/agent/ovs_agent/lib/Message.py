#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent Message encapsulation module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json
from neutron.plugins.centec.agent.ovs_agent.lib.MessageType import MessageType as MsgType
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


class Message(object):
    def __init__(self, version, msg_type, xid, data):
        '''
        init
        :param version: message version
        :param msg_type: message type
        :param xid: identify id
        :param data: python json object.
        '''
        self._version = version
        self._type = msg_type
        self._xid = xid
        self._data = data
        # stand for validity, if color is red, discard
        self._color = CONST.GREEN

    def get_version(self):
        '''
        get message version
        '''
        return self._version

    def get_color(self):
        '''
        get message color
        '''
        return self._color

    def set_color(self, color):
        '''
        set message color
        '''
        self._color = color

    def get_type(self):
        '''
        get message type
        '''
        return self._type

    def get_type_to_string(self):
        '''
        get message type to string
        '''
        if self._type in MsgType.register_msg:
            return MsgType.register_msg[self._type]
        else:
            return "None"

    def get_xid(self):
        '''
        get message xid
        '''
        return self._xid

    def get_data(self):
        '''
        get message data, not json fomatter
        '''
        return self._data

    def string(self):
        '''
        debug info about this message
        '''
        return "version:%d, type:%s(%d), xid:%d, data:%s" % \
               (self._version, self.get_type_to_string(), self.get_type(), self._xid,
                json.dumps(self._data))
