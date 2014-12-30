#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent network infomation in database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json


class NetworkMessage(object):
    def __init__(self, msg):
        '''
        init
        :param msg: Message class
        '''
        self._network_id = None
        self._tenant_id = None
        self._md5sum = None
        self._network_name = None
        self._network_type = None
        self._segmentation_id = None
        self._subnets = set()

        self._encapsulation_message(msg)

    def _encapsulation_message(self, msg):
        '''
        construct network message
        :param msg: Message class
        '''
        for key, value in msg.items():
            # change unicode to string
            key = key.encode("utf-8")

            if "md5sum" == key:
                self._md5sum = value
            elif "network_id" == key:
                self._network_id = value
            elif "tenant_id" == key:
                self._tenant_id = value
            elif "segmentation_id" == key:
                self._segmentation_id = value
            elif "network_name" == key:
                self._network_name = value
            elif "network_type" == key:
                self._network_type = value
            else:
                continue

    def get_network_id(self):
        '''
        get network id
        '''
        return self._network_id

    def get_tenant_id(self):
        '''
        get tenant id
        '''
        return self._tenant_id

    def get_md5sum(self):
        '''
        get md5sum
        '''
        return self._md5sum

    def get_network_name(self):
        '''
        get network name
        '''
        return self._network_name

    def get_network_type(self):
        '''
        get network type
        '''
        return self._network_type

    def get_subnets(self):
        '''
        get subnets in this network
        '''
        return self._subnets

    def set_subnet(self, subnet):
        '''
        add subnet to this network
        :param subnet: subnet id
        '''
        self._subnets.add(subnet)

    def string(self):
        '''
        show message infomation
        '''
        data = {}
        if self._network_id:
            data["tenant_id"] = self._tenant_id
            data["network_id"] = self._network_id
            data["md5sum"] = self._md5sum
            data["network_name"] = self._network_name
            data["network_type"] = self._network_type
            data["segmentation_id"] = self._segmentation_id
            data["subnets"] = []
            for subnet_id in self.get_subnets():
                data["subnets"].append(subnet_id)

        return json.dumps(data)
