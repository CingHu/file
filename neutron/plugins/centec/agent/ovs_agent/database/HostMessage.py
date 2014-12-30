#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent host infomation in database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json


class HostMessage(object):
    def __init__(self, msg):
        '''
        init
        :param msg: Message class
        '''
        self._tor_ip = None

        self._encapsulation_message(msg)

    def _encapsulation_message(self, msg):
        '''
        construct host message
        :param msg: Message class
        '''
        for key in msg:
            self._tor_ip = key

    def get_tor_id(self):
        '''
        get tor ip
        '''
        return self._tor_ip

    def string(self):
        '''
        show message infomation
        '''
        data = {}
        if self._tor_ip:
            data["tor_ip"] = self._tor_ip

        return json.dumps(data)
