#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent vlan infomation in database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json


class VlanMessage(object):
    def __init__(self, msg):
        '''
        init
        :param msg: Message class
        '''
        self._md5sum = None
        self._segmentation_id = None

        self._encapsulation_message(msg)

    def _encapsulation_message(self, msg):
        '''
        construct vlan message
        :param msg: Message class
        '''
        for key, value in msg.items():
            # change unicode to string
            key = key.encode("utf-8")

            if "segmentation_id" == key:
                self._segmentation_id = value
            elif "md5sum" == key:
                self._md5sum = value
            else:
                continue

    def get_vlan_id(self):
        '''
        get vlan id
        '''
        return self._segmentation_id

    def get_md5sum(self):
        '''
        get md5sum
        '''
        return self._md5sum

    def string(self):
        '''
        show message infomation
        '''
        data = {}
        if self._segmentation_id:
            data["segmentation_id"] = self._segmentation_id
            data["md5sum"] = self._md5sum

        return json.dumps(data)
