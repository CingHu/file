#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-bridge-agent CLI
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from cmd import Cmd
import sys
import struct
import json

from neutron.plugins.centec.agent.ovs_agent.lib import hub
from neutron.plugins.centec.agent.ovs_agent.lib.hub import socket
from neutron.plugins.centec.agent.ovs_agent.agentclient.clientlib import Centecclilib as CONST


class base(object):
    is_active = False
    socket = None
    connect_address = None
    connect_count = CONST.CONNECT_COUNT
    client = None


class Client(Cmd):
    # init
    def __init__(self):
        Cmd.__init__(self)

    global base
    prompt = '>>>'

    def _send_command(self, commands):
        base.is_active = True
        json_str = json.dumps(commands)
        data_buffer = bytearray(json_str.encode("utf-8"))

        # encapsulation message (TLV)
        buf = bytearray(CONST.MSG_HEADER_LEN)
        struct.pack_into("!B", buf, 0, CONST.MSG_REQUEST)
        struct.pack_into("!I", buf, 1, CONST.MSG_HEADER_LEN + len(data_buffer))

        buf += data_buffer
        try:
            base.socket.sendall(buf)
        except:
            print "CLI SEND ERROR, EXIT...!"
            base.socket.close()

    def _recv_data(self):
        required_len = CONST.MSG_HEADER_LEN
        buf = bytearray()

        while base.is_active:
            ret = base.socket.recv(required_len)
            if 0 == len(ret):
                print "CLI RECV ERROR, EXIT...!"
                base.socket.close()
                return

            buf += ret

            # recv packet maybe slice
            while len(buf) >= required_len:
                data = buffer(buf[:CONST.MSG_HEADER_LEN])
                (msg_type, msg_len) = struct.unpack('!BI', data)
                required_len = msg_len

                if len(buf) < required_len:
                    break

                print "RECV FROM AGENT"
                msg_data = buf[CONST.MSG_HEADER_LEN: required_len]
                self._show_msg(msg_type, msg_data)

                buf = buf[required_len:]
                required_len = CONST.MSG_HEADER_LEN
                base.is_active = False

    def _show_msg(self, msg_type, data):
        if CONST.MSG_TENANT == msg_type:
            self._print_tenant(data)
        elif CONST.MSG_NETWORK == msg_type:
            self._print_network(data)
        elif CONST.MSG_SUBNET == msg_type:
            self._print_subnet(data)
        elif CONST.MSG_PORT == msg_type:
            self._print_port(data)
        elif CONST.MSG_HOST == msg_type:
            self._print_route(data)
        elif CONST.MSG_VLAN == msg_type:
            self._print_vlan(data)
        elif CONST.MSG_DB == msg_type:
            self._print_db(data)
        else:
            self._print_default(data)

    def _print_tenant(self, data):
        print data

    def _print_network(self, data):
        print data

    def _print_subnet(self, data):
        print data

    def _print_port(self, data):
        print data

    def _print_route(self, data):
        print data

    def _print_vlan(self, data):
        print data

    def _print_db(self, data):
        print data

    def _print_default(self, data):
        print data

    def preloop(self):
        print 'ENTER CLI TOOLS....!'

    def postloop(self):
        print 'QUIT CLI TOOLS.....!'

    def emptyline(self):
        pass

    def do_show(self, arg):
        args = arg.split(' ')
        length = len(args)
        commands = None

        if 3 <= length and 5 > length:
            if '-t' == args[0]:
                tblname = str(args[1])
                print tblname
                if 'all' == args[2]:
                    if length > 3:
                        self.default(0)
                    commands = "show -t %s all" % tblname.upper()
                elif '-p' == args[2]:
                    if length < 4:
                        self.default(0)
                    commands = "show -t %s -p %s" % \
                               (tblname.upper(), str(args[3]))
                else:
                    self.default(0)
            else:
                self.default(0)
        elif 1 == length:
            if 'db' == args[0]:
                commands = "show db"
            else:
                self.default(0)
        else:
            self.default(0)

        if commands:
            self._send_command(commands)
            self._recv_data()

    def help_show(self):
        print 'SHOW DATABASE'

    def default(self, line):
        print 'COMMAND NOT FIND...'

    def do_exit(self):
        sys.exit(1)

    def do_quit(self):
        sys.exit(1)


def _connect():
    '''
    connect to ovs bridge agent
    '''
    print "connect is running"

    global base

    while True:
        try:
            base.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            base.socket.connect(base.connect_address)
        except Exception, e:
            base.connect_count -= 1
            print "CLI TOOLS START ERROR"
            if base.connect_count:
                hub.sleep(CONST.SLEEP_INTERVAL)
                continue
            else:
                return False
        else:
            base.connect_count = CONST.CONNECT_COUNT
            return True


def main():
    base.client = Client()

    base.connect_address = (('localhost', CONST.CLI_PORT))

    _cli = _connect()
    if not _cli:
        return

    try:
        base.client.cmdloop()
    except:
        base.client.postloop()
