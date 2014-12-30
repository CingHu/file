#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent subnet infomation in database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import json


class SubnetMessage(object):
    def __init__(self, msg):
        '''
        init
        :param msg: Message class
        '''
        self._subnet_id = None
        self._tenant_id = None
        self._network_id = None
        self._md5sum = None
        self._enable_dhcp = None
        self._network_mask = None
        self._network = None
        self._dhcp_ip = None
        self._dhcp_mac = None
        self._ip_version = None
        self._shared = None
        self._bc_id = None
        self._ports = set()
        self._gateways = {}

        self._encapsulation_message(msg)

    def _encapsulation_message(self, msg):
        '''
        construct subnet message
        :param msg: Message class
        '''
        for key, value in msg.items():
            # change unicode to string
            key = key.encode("utf-8")

            if key == "md5sum":
                self._md5sum = value
            elif key == "tenant_id":
                self._tenant_id = value
            elif key == "network_id":
                self._network_id = value
            elif key == "subnet_id":
                self._subnet_id = value
            elif key == "network_mask":
                self._network_mask = value
            elif key == "network":
                self._network = value
            elif key == "enable_dhcp":
                self._enable_dhcp = value
            elif key == "ip_version":
                self._ip_version = value
            elif key == "shared":
                self._shared = value
            else:
                continue

    def get_tenant_id(self):
        '''
        get tenant id
        '''
        return self._tenant_id

    def get_subnet_id(self):
        '''
        get subnet id
        '''
        return self._subnet_id

    def get_network_id(self):
        '''
        get network id
        '''
        return self._network_id

    def get_network_mask(self):
        '''
        get network mask in this subnet
        '''
        return self._network_mask

    def get_network(self):
        '''
        get network in this subnet
        '''
        return self._network

    def get_md5sum(self):
        '''
        get md5sum
        '''
        return self._md5sum

    def get_broadcast_id(self):
        '''
        get broadcast id
        '''
        return self._bc_id

    def set_broadcast_id(self, bc_id):
        '''
        set broadcast id
        '''
        self._bc_id = bc_id

    def get_gateways(self):
        '''
        get gateway
        '''
        return self._gateways

    def get_segmentation_id(self):
        '''
        get segmentation id
        '''
        return self._segmentation_id

    def get_dhcp_ip(self):
        '''
        get dhcp ip
        '''
        return self._dhcp_ip

    def set_dhcp_ip(self, ip_addr):
        '''
        set dhcp ip
        :param dhcp ip: ip address
        '''
        self._dhcp_ip = ip_addr

    def get_dhcp_mac(self):
        '''
        get dhcp mac
        '''
        return self._dhcp_mac

    def set_dhcp_mac(self, mac_addr):
        '''
        set dhcp mac
        :param mac_addr: mac address
        '''
        self._dhcp_mac = mac_addr

    def set_gateways(self, router_id, ip_addr, mac_addr, rid):
        '''
        set gateway mac
        :param router_id: router id
        :param mac_addr: mac address
        :param ip_addr: ip address
        '''
        self._gateways[router_id] = {}
        self._gateways[router_id]["mac"] = mac_addr
        self._gateways[router_id]["ip"] = ip_addr
        self._gateways[router_id]["id"] = rid

    def del_gateways(self, router_id):
        '''
        del gateway mac
        :param router_id: router id
        '''
        self._gateways.pop(router_id)

    def get_ports(self):
        '''
        get ports in this subnet
        '''
        return self._ports

    def set_port(self, port):
        '''
        add port to this subnet
        :param port: port id
        '''
        self._ports.add(port)

    def string(self):
        '''
        show message infomation
        '''
        data = {}
        if self._subnet_id:
            data["tenant_id"] = self._tenant_id
            data["network_id"] = self._network_id
            data["subnet_id"] = self._subnet_id
            data["network"] = self._network
            data["md5sum"] = self._md5sum
            data["network_mask"] = self._network_mask
            data["ip_version"] = self._ip_version
            data["enable_dhcp"] = self._enable_dhcp
            data["shared"] = self._shared
            data["gateway"] = self._gateways
            data["dhcp_ip"] = self._dhcp_ip
            data["dhcp_mac"] = self._dhcp_mac
            data["ports"] = []
            for port_id in self.get_ports():
                data["ports"].append(port_id)

        return json.dumps(data)
