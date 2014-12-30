#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-bridge-agent cli server
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import struct
import json
import traceback

import hub
from neutron.plugins.centec.agent.ovs_agent.lib.hub import socket
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


class CliServer(object):
    def __init__(self, db):
        '''
        init
        :param db: database
        '''
        self._db = db
        self._log = Logger("ovs_agent.cli")
        self._cli_th = hub.spawn(self._cli_sercver)

    # cli op
    def _cli_sercver(self):
        '''
        cli thread
        '''

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.bind(("localhost", CONST.CLI_SOCKET_PORT))
        except:
            self._log.error(traceback.format_exc())
            self._socket.close()

        self._socket.listen(1)

        while True:
            connection, address = self._socket.accept()
            self._log.info("address:%s:%s is connect" % address)
            while True:
                buf = connection.recv(1024)
                if 0 == len(buf):
                    self._log.info("address:%s:%s is lost connect" % address)
                    break

                (msg_type, msg_len) = struct.unpack('!BI', buffer(buf[:CONST.CLI_HEADER_LEN]))
                if CONST.CLI_REQUEST == msg_type:
                    msg_data = buf[CONST.CLI_HEADER_LEN: msg_len]
                    msg_data = msg_data[1:-1]
                    self._handle_cli_command(connection, msg_data)
                else:
                    self._send_data(connection, CONST.CLI_ERROR)

    def _send_data(self, connection, msg_type, data=None):
        '''
        send data to cli
        :param connection: cli connection
        :param msg_type: cli message type
        :param data: data
        '''
        if not data:
            data = "None"

        json_str = json.dumps(data)
        data_buffer = bytearray(json_str.encode("utf-8"))

        # encapsulation message (TLV)
        buf = bytearray(CONST.CLI_HEADER_LEN)
        struct.pack_into("!B", buf, 0, msg_type)
        struct.pack_into("!I", buf, 1, CONST.CLI_HEADER_LEN + len(data_buffer))

        buf += data_buffer
        self._log.debug("CLI server send:%s" % len(buf))
        try:
            connection.send(buf)
        except:
            self._log.error(traceback.format_exc())

    def _handle_cli_command(self, connection, data):
        '''
        handle command from cli
        :param connection: cli connection
        :param data: command
        '''
        args = data.split(' ')

        if "show" == args[0]:
            self._show(connection, args)
            return

        self._send_data(connection, CONST.CLI_ERROR)

    def _show(self, connection, args):
        '''
        show data in db
        :param connection: cli connection
        :param args: command args
        '''
        if "-t" == args[1]:
            self._show_table(connection, args)
            return
        elif "db" == args[1]:
            self._show_db(connection)
            return

        return self._send_data(connection, CONST.CLI_ERROR)

    def _show_db(self, connection):
        data = {}
        for table_name in self._db:
            data[table_name] = []
            for key in self._db[table_name]:
                data[table_name].append(key)

        self._send_data(connection, CONST.CLI_DB, data)

    def _show_table(self, connection, args):
        if args[2] == CONST.DBTABLE_TENANT:
            if args[3] == "all":
                self._show_tenant(connection, True)
            else:
                self._show_tenant(connection, False, args[4])
        elif args[2] == CONST.DBTABLE_NETWORK:
            if args[3] == "all":
                self._show_network(connection, True)
            else:
                self._show_network(connection, False, args[4])
        elif args[2] == CONST.DBTABLE_SUBNET:
            if args[3] == "all":
                self._show_subnet(connection, True)
            else:
                self._show_subnet(connection, False, args[4])
        elif args[2] == CONST.DBTABLE_PORT:
            if args[3] == "all":
                self._show_port(connection, True)
            else:
                self._show_port(connection, False, args[4])
        elif args[2] == CONST.DBTABLE_HOST:
            if args[3] == "all":
                self._show_host(connection, True)
            else:
                self._show_host(connection, False, args[4])
        elif args[2] == CONST.DBTABLE_VLAN:
            if args[3] == "all":
                self._show_vlan(connection, True)
            else:
                self._show_vlan(connection, False, args[4])

    def _show_tenant(self, connection, is_all, port_id=None):
        data = {}
        if is_all:
            data[CONST.DBTABLE_TENANT] = []
            for key in self._db[CONST.DBTABLE_TENANT]:
                data[CONST.DBTABLE_TENANT].append(key)
            self._send_data(connection, CONST.CLI_TENANT, data)
        else:
            ports = self._db[CONST.DBTABLE_TENANT]
            if port_id in ports:
                data[CONST.DBTABLE_TENANT] = ports[port_id].string()
                self._send_data(connection, CONST.CLI_TENANT, data)
            else:
                self._send_data(connection, CONST.CLI_ERROR)

    def _show_network(self, connection, is_all, port_id=None):
        data = {}
        if is_all:
            data[CONST.DBTABLE_NETWORK] = []
            for key in self._db[CONST.DBTABLE_NETWORK]:
                data[CONST.DBTABLE_NETWORK].append(key)
            self._send_data(connection, CONST.CLI_NETWORK, data)
        else:
            ports = self._db[CONST.DBTABLE_NETWORK]
            if port_id in ports:
                data[CONST.DBTABLE_NETWORK] = ports[port_id].string()
                self._send_data(connection, CONST.CLI_NETWORK, data)
            else:
                self._send_data(connection, CONST.CLI_ERROR)

    def _show_subnet(self, connection, is_all, port_id=None):
        data = {}
        if is_all:
            data[CONST.DBTABLE_SUBNET] = []
            for key in self._db[CONST.DBTABLE_SUBNET]:
                data[CONST.DBTABLE_SUBNET].append(key)
            self._send_data(connection, CONST.CLI_SUBNET, data)
        else:
            ports = self._db[CONST.DBTABLE_SUBNET]
            if port_id in ports:
                data[CONST.DBTABLE_SUBNET] = ports[port_id].string()
                self._send_data(connection, CONST.CLI_SUBNET, data)
            else:
                self._send_data(connection, CONST.CLI_ERROR)

    def _show_port(self, connection, is_all, port_id=None):
        data = {}
        if is_all:
            data[CONST.DBTABLE_PORT] = []
            for key in self._db[CONST.DBTABLE_PORT]:
                data[CONST.DBTABLE_PORT].append(key)
            self._send_data(connection, CONST.CLI_PORT, data)
        else:
            ports = self._db[CONST.DBTABLE_PORT]
            if port_id in ports:
                data[CONST.DBTABLE_PORT] = ports[port_id].string()
                self._send_data(connection, CONST.CLI_PORT, data)
            else:
                self._send_data(connection, CONST.CLI_ERROR)

    def _show_host(self, connection, is_all, port_id=None):
        data = {}
        if is_all:
            data[CONST.DBTABLE_HOST] = []
            for key in self._db[CONST.DBTABLE_HOST]:
                data[CONST.DBTABLE_HOST].append(key)
            self._send_data(connection, CONST.CLI_HOST, data)
        else:
            ports = self._db[CONST.DBTABLE_HOST]
            if port_id in ports:
                data[CONST.DBTABLE_HOST] = ports[port_id].string()
                self._send_data(connection, CONST.CLI_HOST, data)
            else:
                self._send_data(connection, CONST.CLI_ERROR)

    def _show_vlan(self, connection, is_all, port_id=None):
        data = {}
        if is_all:
            data[CONST.DBTABLE_VLAN] = []
            for key in self._db[CONST.DBTABLE_VLAN]:
                data[CONST.DBTABLE_VLAN].append(key)
            self._send_data(connection, CONST.CLI_VLAN, data)
        else:
            ports = self._db[CONST.DBTABLE_VLAN]
            if port_id in ports:
                data[CONST.DBTABLE_VLAN] = ports[port_id].string()
                self._send_data(connection, CONST.CLI_VLAN, data)
            else:
                self._send_data(connection, CONST.CLI_ERROR)
