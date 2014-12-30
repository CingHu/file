#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent tenant infomation in database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json


class TenantMessage(object):
    def __init__(self, msg):
        '''
        init
        :param msg: Message class
        '''
        self._tenant_id = None
        self._networks = set()

        self._encapsulation_message(msg)

    def _encapsulation_message(self, msg):
        '''
        construct tenant message
        :param msg: Message class
        '''
        for key, value in msg.items():
            # change unicode to string
            key = key.encode("utf-8")

            if "tenant_id" == key:
                self._tenant_id = value
                break

    def get_tenant_id(self):
        '''
        get tenant id
        '''
        return self._tenant_id

    def get_networks(self):
        '''
        get networks in this tenant
        '''
        return self._networks

    def set_network(self, network):
        '''
        add network to this tenant
        :param network: network id
        '''
        self._networks.add(network)

    def string(self):
        '''
        show message infomation
        '''
        data = {}
        if self._tenant_id:
            data["tenant_id"] = self._tenant_id
            data["networks"] = []
            for network_id in self.get_networks():
                data["networks"].append(network_id)

        return json.dumps(data)
