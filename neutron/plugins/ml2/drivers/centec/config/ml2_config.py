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
# @author: Yi Zhao Centec Networks, Inc.

from oslo.config import cfg
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)

MANAGER_IP = '127.0.0.1'
MANAGER_NB_PORT = 16889
MANAGER_SB_PORT = 16888
MANAGER_VLAN_ALLOC_TYPE_NETWORK = 'network'
MANAGER_VLAN_ALLOC_TYPE_TENANT = 'tenant'
MANAGER_LOG_FILE = '/var/log/neutron/centec-cloud-switch-manager.log'

MANAGER_IP_STR = 'rpc_ip'
MANAGER_NB_PORT_STR = 'nb_port'
MANAGER_SB_PORT_STR = 'sb_port'
MANAGER_AUTO_START_STR = 'auto_start'
MANAGER_ROOT_HELPER_STR = 'root_helper'
MANAGER_REMOTE_DEBUG_STR = 'remote_debug'
MANAGER_VERBOSE_STR = 'verbose'
MANAGER_DEBUG_STR = 'debug'
MANAGER_VLAN_ALLOC_TYPE_STR = 'vlan_alloc_type'
MANAGER_LOG_FILE_STR = 'log_file'
MANAGER_CONNECTION_STR = 'connection'

ml2_centec_opts = [
    cfg.StrOpt(MANAGER_IP_STR, default=MANAGER_IP,
               help=_("configure Centec manager IP address")),
    cfg.IntOpt(MANAGER_NB_PORT_STR, default=MANAGER_NB_PORT,
               help=_("configure Centec manager northbound port")),
    cfg.IntOpt(MANAGER_SB_PORT_STR, default=MANAGER_SB_PORT,
               help=_("configure Centec manager southbound port")),
]

cfg.CONF.register_opts(ml2_centec_opts, "centec")


class CentecML2MechConfig(object):
    """
    ML2 Mechanism Driver - Centec Configuration class.
    """

    def __init__(self):
        """
        Init
        """
        self.__manager_ip = MANAGER_IP
        self.__manager_nb_port = MANAGER_NB_PORT
        self.__manager_sb_port = MANAGER_SB_PORT
        self.__manager_auto_start = True
        self.__manager_verbose = False
        self.__manager_debug = False
        self.__manager_vlan_alloc_type = MANAGER_VLAN_ALLOC_TYPE_NETWORK
        self.__manager_root_helper = None
        self.__manager_remote_debug = False
        self.__manager_log_file = MANAGER_LOG_FILE
        self.config_files = self.get_config_file_args(cfg.CONF.config_file)
        try:
            self.__create_config()
        except:
            LOG.error('Wrong values in parsing options: [ml2_centec]')

    def __validate_config(self):
        """
        validate configurations
        """
        pass

    def get_manager_rpc_ip(self):
        """
        Get manager RPC IP address
        """
        return self.__manager_ip

    def get_manager_nb_port(self):
        """
        Get manager northbound port
        """
        return self.__manager_nb_port

    def get_manager_sb_port(self):
        """
        Get manager southbound port
        """
        return self.__manager_sb_port

    def get_manager_auto_start(self):
        """
        Get manager auto start flag
        """
        return self.__manager_auto_start

    def get_manager_remote_debug(self):
        """
        Get manager remote debug flag
        """
        return self.__manager_remote_debug

    def get_manager_verbose(self):
        """
        Get manager verbose flag
        """
        return self.__manager_verbose

    def get_manager_debug(self):
        """
        Get manager debug flag
        """
        return self.__manager_debug

    def get_manager_vlan_alloc_type(self):
        """
        Get vlan allocation type
        """
        return self.__manager_vlan_alloc_type

    def get_manager_root_helper(self):
        """
        Get manager root helper
        """
        return self.__manager_root_helper

    def get_manager_log_file(self):
        """
        Get manager log file
        """
        return self.__manager_log_file

    def get_config_file_args(self, config_files):
        """
        Get config file args
        :param config_files: config files
        """
        config_file_args = []
        for config_file in config_files:
            config_file_args = config_file_args + ['--config-file'] + [config_file] 
        return config_file_args

    def __create_config(self):
        """
        Parse config files and create configs
        """
        agent_root_helper = None

        multi_parser = cfg.MultiConfigParser()
        read_ok = multi_parser.read(cfg.CONF.config_file)

        if len(read_ok) != len(cfg.CONF.config_file):
            raise cfg.Error(_("Some config files were not parsed properly"))
        self.__validate_config()

        for parsed_file in multi_parser.parsed:
            for parsed_item in parsed_file.keys():
                if parsed_item.lower() == 'agent':
                    for key, value in parsed_file[parsed_item].items():
                        if key.lower() == MANAGER_ROOT_HELPER_STR:
                            agent_root_helper = value[0]
                if parsed_item.lower() == 'database':
                    for key, value in parsed_file[parsed_item].items():
                        if key.lower() == MANAGER_CONNECTION_STR:
                            database_connection = value[0]
                if parsed_item.lower() == 'centec':
                    for key, value in parsed_file[parsed_item].items():
                        if key.lower() == MANAGER_IP_STR:
                            self.__manager_ip = value[0]
                        if key.lower() == MANAGER_NB_PORT_STR:
                            self.__manager_nb_port = value[0]
                        if key.lower() == MANAGER_SB_PORT_STR:
                            self.__manager_sb_port = value[0]
                        if key.lower() == MANAGER_AUTO_START_STR:
                            self.__manager_auto_start = (str(value[0]).lower() == 'true')
                        if key.lower() == MANAGER_REMOTE_DEBUG_STR:
                            self.__manager_remote_debug = (str(value[0]).lower() == 'true')
                        if key.lower() == MANAGER_VERBOSE_STR:
                            self.__manager_verbose = (str(value[0]).lower() == 'true')
                        if key.lower() == MANAGER_DEBUG_STR:
                            self.__manager_debug = (str(value[0]).lower() == 'true')
                        if key.lower() == MANAGER_VLAN_ALLOC_TYPE_STR:
                            self.__manager_vlan_alloc_type = value[0]
                        if key.lower() == MANAGER_ROOT_HELPER_STR:
                            self.__manager_root_helper = value[0]
                        if key.lower() == MANAGER_LOG_FILE_STR:
                            self.__manager_log_file = value[0]
        if self.__manager_root_helper is None:
            if agent_root_helper is None:
                self.__manager_root_helper = 'sudo'
            else:
                self.__manager_root_helper = agent_root_helper
