#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent database
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from neutron.plugins.centec.agent.ovs_agent.lib.CliServer import CliServer
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


class Database(object):
    def __init__(self, tables=None):
        '''
        init
        :param tables: table name
        '''
        self._dataBase = {}
        if tables:
            for table in tables:
                self._dataBase[table] = {}

        self._log = Logger("ovs_agent.database")
        self._cli = CliServer(self._dataBase)

    # db op
    def add_entry_to_db(self, table_type, key, key_info):
        '''
        add data to db
        :param table_type: table name
        :param key: table key
        :param key_info:table key associate data
        '''
        self._log.debug("DB: %s add %s" % (table_type, key))
        self._dataBase[table_type][key] = key_info

    def del_entry_from_db(self, table_type, key):
        '''
        delete data from db
        :param table_type: table name
        :param key: table key
        '''
        if table_type in self._dataBase:
            self._log.debug("DB: %s remove %s" % (table_type, key))
            self._dataBase[table_type].pop(key)

    def update_entry_to_db(self, table_type, key, key_info):
        '''
        update data to db
        :param table_type: table name
        :param key: table key
        :param key_info:table key associate data
        '''
        self._log.debug("DB: %s update %s" % (table_type, key))
        old_info = self._dataBase[table_type][key]

        if CONST.DBTABLE_NETWORK == table_type:
            for subnet_id in old_info.get_subnets():
                key_info.set_subnet(subnet_id)

            self._dataBase[table_type][key] = key_info
        elif CONST.DBTABLE_SUBNET == table_type:
            for port_id in old_info.get_ports():
                key_info.set_port(port_id)

            dhcp_ip = old_info.get_dhcp_ip()
            key_info.set_dhcp_ip(dhcp_ip)

            dhcp_mac = old_info.get_dhcp_mac()
            key_info.set_dhcp_mac(dhcp_mac)

            for router_id in old_info.get_gateways():
                r_mac = old_info.get_gateways()[router_id]["mac"]
                r_ip = old_info.get_gateways()[router_id]["ip"]
                r_id = old_info.get_gateways()[router_id]["id"]
                key_info.set_gateways(router_id, r_ip, r_mac, r_id)

            self._dataBase[table_type][key] = key_info
        elif CONST.DBTABLE_PORT == table_type:
            ofport_id = old_info.get_ofport_id()
            key_info.set_ofport_id(ofport_id)
            self._dataBase[table_type][key] = key_info
        else:
            self._dataBase[table_type][key] = key_info

    # db lookup
    def lookup_entry_from_db(self, table_type, key):
        '''
        lookup data whether in db
        :param table_type: table name
        :param key: table key
        '''
        if table_type in self._dataBase:
            if key in self._dataBase[table_type]:
                return True, self._dataBase[table_type][key]
        return False, None

    def lookup_table_from_db(self, table_type):
        '''
        lookup table whether in db
        :param table_type: table name
        '''
        if table_type in self._dataBase:
            return self._dataBase[table_type]
        return None

    def clear_table_from_db(self, table_type):
        '''
        clear table data in db
        :param table_type: table name
        '''
        if table_type in self._dataBase:
            self._dataBase[table_type].clear()
