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

from abc import ABCMeta

import six


@six.add_metaclass(ABCMeta)
class ProtocolDriver(object):
    """
    Define Protocol driver used in Centec TOR switch
    """

    def get_switch_local_vlan_id(self, context):
        """
        Get switch local vlan id
        :param context: context
        """
        pass

    def get_connected_switch(self, context):
        """
        Get connected switch
        :param context: context
        """
        pass

    def create_network(self, context):
        '''
        Create network
        @param context: network context
        '''
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
