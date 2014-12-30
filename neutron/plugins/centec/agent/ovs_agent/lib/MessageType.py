#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent Message type
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


def parse_msg_type(msg_type, sub_type):
        return (msg_type << 5) + sub_type


class MessageType(object):
    ''' Message Type class '''

    # Message type from manager to agent
    MSG_CREATE_NETWORK = parse_msg_type(CONST.MANAGER_MSG, CONST.CREATE_NETWORK)
    MSG_UPDATE_NETWORK = parse_msg_type(CONST.MANAGER_MSG, CONST.UPDATE_NETWORK)
    MSG_DELETE_NETWORK = parse_msg_type(CONST.MANAGER_MSG, CONST.DELETE_NETWORK)

    MSG_CREATE_SUBNET = parse_msg_type(CONST.MANAGER_MSG, CONST.CREATE_SUBNET)
    MSG_UPDATE_SUBNET = parse_msg_type(CONST.MANAGER_MSG, CONST.UPDATE_SUBNET)
    MSG_DELETE_SUBNET = parse_msg_type(CONST.MANAGER_MSG, CONST.DELETE_SUBNET)

    MSG_CREATE_PORT = parse_msg_type(CONST.MANAGER_MSG, CONST.CREATE_PORT)
    MSG_UPDATE_PORT = parse_msg_type(CONST.MANAGER_MSG, CONST.UPDATE_PORT)
    MSG_DELETE_PORT = parse_msg_type(CONST.MANAGER_MSG, CONST.DELETE_PORT)

    MSG_CREATE_VLAN = parse_msg_type(CONST.MANAGER_MSG, CONST.CREATE_TENANT_SEGMENT)
    MSG_UPDATE_VLAN = parse_msg_type(CONST.MANAGER_MSG, CONST.UPDATE_TENANT_SEGMENT)
    MSG_DELETE_VLAN = parse_msg_type(CONST.MANAGER_MSG, CONST.DELETE_TENANT_SEGMENT)

    MSG_UPDATE_LINK = parse_msg_type(CONST.MANAGER_MSG, CONST.HOST_TOR_CONNECTION)

    MSG_REPLY_NETWORK = parse_msg_type(CONST.MANAGER_MSG, CONST.REPLY_NETWORK)
    MSG_REPLY_SUBNET = parse_msg_type(CONST.MANAGER_MSG, CONST.REPLY_SUBNET)
    MSG_REPLY_PORT = parse_msg_type(CONST.MANAGER_MSG, CONST.REPLY_PORT)
    MSG_REPLY_VLAN = parse_msg_type(CONST.MANAGER_MSG, CONST.REPLY_TENANT_SEGMENT)
    MSG_REPLY_LINK = parse_msg_type(CONST.MANAGER_MSG, CONST.REPLY_HOST_TOR_CONNT)
    MSG_REPLY_ERROR = parse_msg_type(CONST.MANAGER_MSG, CONST.REPLY_ERROR)

    # Message type from agent to manager
    MSG_REQUEST_NETWORK = parse_msg_type(CONST.AGENT_MSG, CONST.REQUEST_NETWORK)
    MSG_REQUEST_SUBNET = parse_msg_type(CONST.AGENT_MSG, CONST.REQUEST_SUBNET)
    MSG_REQUEST_PORT = parse_msg_type(CONST.AGENT_MSG, CONST.REQUEST_PORT)
    MSG_REQUEST_VLAN = parse_msg_type(CONST.AGENT_MSG, CONST.REQUEST_TENANT_SEGMENT)
    MSG_REQUEST_LINK = parse_msg_type(CONST.AGENT_MSG, CONST.REQUEST_HOST_TOR_CONNT)

    register_msg = {
        MSG_REPLY_NETWORK: "REPLY_NETWORK",
        MSG_REPLY_SUBNET: "REPLY_SUBNET",
        MSG_REPLY_PORT: "REPLY_PORT",
        MSG_REPLY_VLAN: "REPLY_VLAN",
        MSG_REPLY_ERROR: "REPLY_ERROR",
        MSG_REPLY_LINK: "REPLY_LINK",

        MSG_REQUEST_NETWORK: "REQUEST_NETWORK",
        MSG_REQUEST_SUBNET: "REQUEST_SUBNET",
        MSG_REQUEST_PORT: "REQUEST_PORT",
        MSG_REQUEST_VLAN: "REQUEST_VLAN",
        MSG_REQUEST_LINK: "REQUEST_LINK",

        MSG_CREATE_NETWORK: "CREATE_NETWORK",
        MSG_DELETE_NETWORK: "DELETE_NETWORK",
        MSG_CREATE_SUBNET: "CREATE_SUBNET",
        MSG_DELETE_SUBNET: "DELETE_SUBNET",
        MSG_CREATE_PORT: "CREATE_PORT",
        MSG_DELETE_PORT: "DELETE_POTR",
        MSG_CREATE_VLAN: "CREATE_VLAN",
        MSG_DELETE_VLAN: "DELETE_VLAN",

        MSG_UPDATE_NETWORK: "UPDATE_NETWORK",
        MSG_UPDATE_SUBNET: "UPDATE_SUBNET",
        MSG_UPDATE_PORT: "UPDATE_PORT",
        MSG_UPDATE_VLAN: "UPDATE_VLAN",
        MSG_UPDATE_LINK: "UPDATE_LINK",
    }
