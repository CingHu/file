#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      CLI Global configure file
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''


class Centecclilib(object):
    CONNECT_COUNT = 10
    SLEEP_INTERVAL = 2
    Q_LENGTH = 16

    MSG_HEADER_LEN = 5

    MSG_REQUEST = 0
    MSG_TENANT = 1
    MSG_NETWORK = 2
    MSG_SUBNET = 3
    MSG_PORT = 4
    MSG_VLAN = 5
    MSG_HOST = 6
    MSG_DB = 7
    MSG_ERROR = 15

    CLI_PORT = 17777
