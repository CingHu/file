#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent ovs-agent IO driver
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from oslo.config import cfg
from neutron.agent.linux import utils
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger


class Driver(object):
    def __init__(self):
        '''
        init, get bridge
        '''
        self._log = Logger("ovs_agent.driver")
        self._br_name = cfg.CONF.AGENT.integration_bridge
        self._root_helper = cfg.CONF.AGENT.root_helper

    def del_all_groups(self):
        '''
        delete all of groups in bridge
        '''
        command = ["ovs-ofctl", "del-groups", self._br_name,
                   "-O", "OpenFlow13"]
        try:
            utils.execute(command, self._root_helper)
        except:
            self._log("Execute:%s error..!" % command)

    def write_add_flow(self, data, group=False):
        '''
        wirte add data to io
        :param data: command set()
        '''
        if not data:
            return

        if group:
            for flow in data:
                command = ["ovs-ofctl", "add-group", self._br_name,
                           flow.encode("utf-8"), "-O", "OpenFlow13"]
                try:
                    utils.execute(command, self._root_helper)
                except:
                    self._log("Execute:%s error..!" % command)
        else:
            for flow in data:
                command = ["ovs-ofctl", "add-flow", self._br_name,
                           flow.encode("utf-8"), "-O", "OpenFlow13"]
                try:
                    utils.execute(command, self._root_helper)
                except:
                    self._log("Execute:%s error..!" % command)

    def write_mod_flow(self, data, group=False):
        '''
        wirte mod data to io
        :param data: command set()
        '''
        if not data:
            return

        if group:
            for flow in data:
                command = ["ovs-ofctl", "mod-group", "--strict", self._br_name,
                           flow.encode("utf-8"), "-O", "OpenFlow13"]
                try:
                    utils.execute(command, self._root_helper)
                except:
                    self._log("Execute:%s error..!" % command)
        else:
            for flow in data:
                command = ["ovs-ofctl", "mod-flows", "--strict", self._br_name,
                           flow.encode("utf-8"), "-O", "OpenFlow13"]
                try:
                    utils.execute(command, self._root_helper)
                except:
                    self._log("Execute:%s error..!" % command)

    def write_del_flow(self, data, group=False):
        '''
        wirte del data to io
        :param data: command set()
        '''
        if not data:
            return

        if group:
            for flow in data:
                flow = flow.split("type")[0]
                command = ["ovs-ofctl", "del-groups", "--strict", self._br_name,
                           flow.encode("utf-8"), "-O", "OpenFlow13"]
                try:
                    utils.execute(command, self._root_helper)
                except:
                    self._log("Execute:%s error..!" % command)
        else:
            for flow in data:
                flow = flow.split("actions")[0]
                command = ["ovs-ofctl", "del-flows", "--strict", self._br_name,
                           flow.encode("utf-8"), "-O", "OpenFlow13"]
                try:
                    utils.execute(command, self._root_helper)
                except:
                    self._log("Execute:%s error..!" % command)
