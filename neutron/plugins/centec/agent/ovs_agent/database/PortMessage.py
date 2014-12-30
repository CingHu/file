#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent port infomation in database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json


class PortMessage(object):
    def __init__(self, msg):
        '''
        init
        :param msg: Message class
        '''
        self._port_id = None
        self._md5sum = None
        self._ip = None
        self._mac = None
        self._tenant_id = None
        self._network_id = None
        self._subnet_id = None
        self._device_owner = None
        self._host_name = None
        self._device_id = None
        self._ofport = None
        self._admin_state_up = None

        self._encapsulation_message(msg)

    def _encapsulation_message(self, msg):
        '''
        construct port message
        :param msg: Message class
        '''
        for key, value in msg.items():
            # change unicode to string
            key = key.encode("utf-8")

            if key == "tenant_id":
                self._tenant_id = value
            elif key == "network_id":
                self._network_id = value
            elif key == "subnet_id":
                self._subnet_id = value
            elif key == "port_id":
                self._port_id = value
            elif key == "md5sum":
                self._md5sum = value
            elif key == "device_owner":
                self._device_owner = value
            elif key == "device_id":
                self._device_id = value
            elif key == "ip_address":
                self._ip = value
            elif key == "mac":
                self._mac = value
            elif key == "host_name":
                self._host_name = value
            elif key == "admin_state_up":
                self._admin_state_up = value
            else:
                continue

    def get_tenant_id(self):
        '''
        get tenant id
        '''
        return self._tenant_id

    def get_network_id(self):
        '''
        get network id
        '''
        return self._network_id

    def get_subnet_id(self):
        '''
        get subnet id
        '''
        return self._subnet_id

    def get_md5sum(self):
        '''
        get md5sum
        '''
        return self._md5sum

    def get_port_id(self):
        '''
        get port od
        '''
        return self._port_id

    def get_ip_addr(self):
        '''
        get ip address
        '''
        return self._ip

    def get_mac_addr(self):
        '''
        get mac address
        '''
        return self._mac

    def get_device_owner(self):
        '''
        get port type
        '''
        return self._device_owner

    def get_device_id(self):
        '''
        get router id
        '''
        return self._device_id

    def get_host_name(self):
        '''
        get server name
        '''
        return self._host_name

    def get_admin_state(self):
        '''
        get admin state
        '''
        return self._admin_state_up

    def get_ofport_id(self):
        '''
        get this port associate ofport
        '''
        return self._ofport

    def set_ofport_id(self, ofport_id):
        '''
        get this port associate ofport
        :param ofport_id: ofport id
        '''
        self._ofport = ofport_id

    def string(self):
        '''
        show message infomation
        '''
        data = {}
        if self._port_id:
            data["tenant_id"] = self._tenant_id
            data["network_id"] = self._network_id
            data["subnet_id"] = self._subnet_id
            data["port_id"] = self._port_id
            data["md5sum"] = self._md5sum
            data["mac"] = self._mac
            data["ip_address"] = self._ip
            data["device_owner"] = self._device_owner
            data["host_name"] = self._host_name
            data["device_id"] = self._device_id
            data["ofport"] = self._ofport
            data["admin_state"] = self._admin_state_up

        return json.dumps(data)
