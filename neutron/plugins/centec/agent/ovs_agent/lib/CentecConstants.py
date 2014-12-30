#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      Global configure file
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''


class CentecConstants(object):
    # console Color
    CANCEL_COLOR = '\033[0m'
    WARNNING = '\033[5;32;41m'
    NORMAL = '\033[1;41;41m'

    # Message Length
    MSG_VERSION = 1

    MSG_HEADER_LENGTH = 8
    MSG_HEADER_VERSION_LENGTH = 1
    MSG_HEADER_TYPE_LENGTH = 1
    MSG_HEADER_XID_LENGTH = 2
    # MESSAGE_TYPE(2byte) + MESSAGE_LENGTH(2byte)
    # Note, MESSAGE_LENGTH contains the header length.
    MSG_HEADER_PACK_STR = "!BBHI"

    # Message Type
    MANAGER_MSG = 1  # manager to agent message
    AGENT_MSG = 2  # agent to manager message

    REQUEST_NETWORK = 1  # requests network brief info to manager
    REQUEST_SUBNET = 2  # requests subnet brief info to manager
    REQUEST_PORT = 3  # requests port brief info to manager
    REQUEST_HOST_TOR_CONNT = 6  # Agent requests host-tor-connection brief info to manager
    REQUEST_TENANT_SEGMENT = 8  # Agent requests tenant segm

    REPLY_NETWORK = 20  # reply network brief info(UUID + checksum) to agent
    REPLY_SUBNET = 21  # reply subneGW_PRO = 2000t brief info(UUID + checksum) to agent
    REPLY_PORT = 22  # reply port brief info(UUID + checksum) to agent
    REPLY_ERROR = 27  # reply error message
    REPLY_HOST_TOR_CONNT = 24  # reply host tor connection
    REPLY_TENANT_SEGMENT = 28  # reply tenant segment brief info(UUID + checksum) to agent

    CREATE_NETWORK = 1  # create network type
    UPDATE_NETWORK = 2  # update network type
    DELETE_NETWORK = 3  # delete network type

    CREATE_SUBNET = 4  # create subnet type
    UPDATE_SUBNET = 5  # update subnet type
    DELETE_SUBNET = 6  # delete subnet type

    CREATE_PORT = 7  # create port type
    UPDATE_PORT = 8  # update port type
    DELETE_PORT = 9  # delete port type

    CREATE_TENANT_SEGMENT = 16  # create tenant segment
    UPDATE_TENANT_SEGMENT = 17  # update tenant segment
    DELETE_TENANT_SEGMENT = 18  # delete tenant segment

    HOST_TOR_CONNECTION = 14  # host tor connection

    # Sleep Time
    AGENT_SLEEP_INTERVAL = 2
    SYNC_SLEEP_INTERVAL = 1
    TOPO_SLEEP_INTERVAL = 1
    DB_SLEEP_INTERVAL = 0.01
    RPC_SLEEP_INTERVAL = 1

    DB_TIMEOUT = 60000

    # Database Table Name
    DBTABLE_TENANT = "TENANT"
    DBTABLE_NETWORK = "NETWORK"
    DBTABLE_SUBNET = "SUBNET"
    DBTABLE_PORT = "PORT"
    DBTABLE_VLAN = "VLAN"
    DBTABLE_HOST = "HOST"

    # port type
    IF_ROUTER = "network:router_interface"
    IF_GW = "network:router_gateway"
    IF_DHCP = "network:dhcp"
    IF_FLOAT = "network:floatingip"
    IF_NOVA = "compute:nova"

    # Flow Priority
    GW_PRO = 2000
    UNITCAST_PRO = 1000
    DEF_ROUTE_PRO = 500
    ARP_PRO = 500
    BROADCAST_PRO = 100
    MISSRULE_PRO = 1

    # Log Fomatter
    CONSOLELOGFOMATTER = "%(asctime)s  %(module)s   %(levelname)s  %(message)s"
    FILELOGFOMATTER = "%(asctime)s    %(module)s   %(levelname)s   %(message)s"

    # message color
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    # cli message
    CLI_SOCKET_PORT = 17777
    CLI_HEADER_LEN = 5

    CLI_REQUEST = 0
    CLI_TENANT = 1
    CLI_NETWORK = 2
    CLI_SUBNET = 3
    CLI_PORT = 4
    CLI_VLAN = 5
    CLI_HOST = 6
    CLI_DB = 7
    CLI_ERROR = 15

    # The default respawn interval for the ovsdb monitor
    DEFAULT_OVSDBMON_RESPAWN = 30
    DEFAULT_VLAN = "1"
