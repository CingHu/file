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

from neutron.plugins.ml2.drivers.centec.mechanism_driver.protocol_driver.protocol_driver import ProtocolDriver


class XmppDriver(ProtocolDriver):
    """
    Define XMPP RPC Protocol driver used in Centec TOR switch
    """

    def __init__(self):
        '''
        Init
        '''
        pass

    def create_network(self, context):
        '''
        Create network
        @param context: network context
        '''
        print "XMPP CREATE NETWORK"
        pass

    def update_network(self, context):
        '''
        Update network
        @param context: network context
        '''
        pass

    def delete_network(self, context):
        '''
        Delete network
        @param context: network context
        '''
        pass

    def create_port(self, context):
        '''
        Create port
        @param context: port context
        '''
        pass

    def update_port(self, context):
        '''
        Update port
        @param context: port context
        '''
        pass

    def delete_port(self, context):
        '''
        Delete port
        @param context: port context
        '''
        pass

    def create_subnet(self, context):
        '''
        Create subnet
        @param context: subnet context
        '''
        pass

    def update_subnet(self, context):
        '''
        Update subnet
        @param context: subnet context
        '''
        pass

    def delete_subnet(self, context):
        '''
        Delete subnet
        @param context: subnet context
        '''
        pass
