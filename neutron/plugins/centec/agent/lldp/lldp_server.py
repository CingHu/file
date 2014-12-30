#!/usr/bin/env python
# Copyright (C) 2014 CentecNetworks, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# @author: Yi Zhao, Centec Networks, Inc.
# @author: Zhang Dongya, Centec Networks, Inc.

import threading
import socket
import struct
import fcntl

from neutron.agent.linux import utils
from neutron.plugins.centec.agent.lldp.Packet_Generator import create_packet


def _get_interface_hwaddr(ifname):
    '''
    Get interface hw address
    :param ifname:
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]


class LldpServer():
    '''
    LLDP Server class
    '''

    packet = None
    interface_name = "eth1"
    host_name = "host1"
    chassis_id = "00:00:00:00:00:01"
    port_id = "00:00:00:00:00:02"

    def __init__(self, interface_name=None, root_helper=None):
        '''
        Init method
        :param interface_name: nic interface_name
        :param lldp_send_interval: lldp send interval in seconds
        '''
        self.interface_name = interface_name
        self.port_id = _get_interface_hwaddr(self.interface_name)
        self.chassis_id = self.port_id
        self.host_name = socket.gethostname()

        self.root_helper = root_helper

    def send_packet(self):
        '''
        Construct packet
        @summary: 'sudo python tool.py -p lldp -i eth1 -tlv sys-name host1 -tlv chid -mac-addr 00:00:00:00:00:01 -tlv port-id -mac-addr 00:00:00:00:00:02'
        '''
        # call neutron-centec-send-lldp to send the packet.
        # the console script is built from lldp_send_packet_util.py.
        # must be called with root_helper
        cmd = ["neutron-centec-send-lldp", "-p", "lldp", "-i", self.interface_name, "-tlv", "sys-name", self.host_name,
               "-tlv", "chid", "-mac-addr", self.chassis_id, "-tlv", "port-id",
               "-mac-addr", self.port_id]
        # XXX: add log here.
        utils.execute(cmd, self.root_helper)
