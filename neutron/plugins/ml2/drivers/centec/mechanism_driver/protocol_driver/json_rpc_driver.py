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

from cloud_manager.manager.core.error import CentecError
import json
import jsonrpclib
import logging
from neutron.plugins.ml2.drivers.centec.config.constants import CentecConstant
from neutron.plugins.ml2.drivers.centec.mechanism_driver.protocol_driver.protocol_driver import ProtocolDriver


LOG = logging.getLogger(__name__)


class JsonRpcDriver(ProtocolDriver):
    """
    Define JSON RPC Protocol driver used in Centec TOR switch
    """

    def __init__(self, manager_ip, manager_port):
        '''
        Init
        '''
        LOG.info("Centec JSON RPC driver init")
        self.manager_ip = str(manager_ip)
        self.manager_port = CentecConstant.JSON_RPC_PORT
        if isinstance(manager_port, int):
            self.manager_port = manager_port

    def connect(self):
        """
        Connect json rpc server
        """
        json_rpc_uri = 'http://%s:%s' % (self.manager_ip, self.manager_port)
        server = jsonrpclib.Server(json_rpc_uri)
        return server

    def get_switch_local_vlan_id(self, context):
        """
        Get switch local vlan id
        :param context: context
        """
        LOG.info("get_switch_local_vlan_id: %s", context)
        server = self.connect()
        return server.get_switch_local_vlan_id(context)

    def get_connected_switch(self, context):
        """
        Get connected switch
        :param context: context
        """
        LOG.info("get_connected_switch: %s", context)
        server = self.connect()
        return server.get_connected_switch(context)

    def create_network(self, context):
        '''
        Create network
        @param context: network context
        '''
        LOG.info("create_network: %s", context)
        server = self.connect()
        server._notify.create_network(context)

    def update_network(self, context):
        '''
        Update network
        @param context: network context
        '''
        LOG.info("update_network: %s", context)
        server = self.connect()
        server._notify.update_network(context)

    def delete_network(self, context):
        '''
        Delete network
        @param context: network context
        '''
        LOG.info("delete_network: %s", context)
        server = self.connect()
        server._notify.delete_network(context)

    def create_port(self, context):
        '''
        Create port
        @param context: port context
        '''
        LOG.info("create_port: %s", context)
        server = self.connect()
        response = server.create_port(context)
        response_context = json.loads(str(response))
        error_code = response_context.get('errorCode', CentecError.CENTEC_ERROR_SUCCESS)
        if error_code != CentecError.CENTEC_ERROR_SUCCESS:
            error_desc = response_context.get('errorDesc', '')
            LOG.exception(
                _("Centec driver error: failed to create_port - %s")
                % error_desc)
            raise Exception(
                _("Centec driver error: failed to create_port - %s")
                % error_desc)

    def update_port(self, context):
        '''
        Update port
        @param context: port context
        '''
        LOG.info("update_port: %s", context)
        server = self.connect()
        response = server.update_port(context)
        response_context = json.loads(str(response))
        error_code = response_context.get('errorCode', CentecError.CENTEC_ERROR_SUCCESS)
        if error_code != CentecError.CENTEC_ERROR_SUCCESS:
            error_desc = response_context.get('errorDesc', '')
            LOG.exception(
                _("Centec driver error: failed to update_port - %s")
                % error_desc)
            raise Exception(
                _("Centec driver error: failed to update_port - %s")
                % error_desc)

    def delete_port(self, context):
        '''
        Delete port
        @param context: port context
        '''
        LOG.info("delete_port: %s", context)
        server = self.connect()
        response = server.delete_port(context)
        response_context = json.loads(str(response))
        error_code = response_context.get('errorCode', CentecError.CENTEC_ERROR_SUCCESS)
        if error_code != CentecError.CENTEC_ERROR_SUCCESS:
            error_desc = response_context.get('errorDesc', '')
            LOG.exception(
                _("Centec driver error: failed to delete_port - %s")
                % error_desc)
            raise Exception(
                _("Centec driver error: failed to delete_port - %s")
                % error_desc)

    def create_subnet(self, context):
        '''
        Create subnet
        @param context: subnet context
        '''
        LOG.info("create_subnet: %s", context)
        server = self.connect()
        server._notify.create_subnet(context)

    def update_subnet(self, context):
        '''
        Update subnet
        @param context: subnet context
        '''
        LOG.info("update_subnet: %s", context)
        server = self.connect()
        server._notify.update_subnet(context)

    def delete_subnet(self, context):
        '''
        Delete subnet
        @param context: subnet context
        '''
        LOG.info("delete_subnet: %s", context)
        server = self.connect()
        server._notify.delete_subnet(context)
