#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent flow service
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from neutron.plugins.centec.agent.ovs_agent.drv.Driver import Driver
from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger


class FlowService(object):
    def __init__(self):
        '''
        init flow db
        '''
        self._log = Logger("ovs_agent.flow")
        self._drv = Driver()
        self._flow_tree = {}
        self._compare_tree = {}
        self._construct_tree()

    def _construct_tree(self):
        '''
        construct compare db
        '''
        self._flow_tree["MISS"] = set()
        self._compare_tree["IDENTIFY"] = {}
        self._compare_tree["IDENTIFY"]["ADD"] = set()
        self._compare_tree["IDENTIFY"]["MOD"] = set()
        self._compare_tree["IDENTIFY"]["EXIST"] = set()
        self._compare_tree["FORWARD"] = {}
        self._compare_tree["FORWARD"]["ADD"] = set()
        self._compare_tree["FORWARD"]["MOD"] = set()
        self._compare_tree["FORWARD"]["EXIST"] = set()
        self._compare_tree["ROUTE"] = {}
        self._compare_tree["ROUTE"]["ADD"] = set()
        self._compare_tree["ROUTE"]["MOD"] = set()
        self._compare_tree["ROUTE"]["EXIST"] = set()
        self._compare_tree["GROUP"] = {}
        self._compare_tree["GROUP"]["ADD"] = set()
        self._compare_tree["GROUP"]["MOD"] = set()
        self._compare_tree["GROUP"]["EXIST"] = set()

    def del_all_groups(self):
        '''
        delete all of groups
        '''
        self._drv.del_all_groups()

    def add_miss_flow(self, flow):
        '''
        add missrule flow
        :param flow:
        '''
        self._flow_tree["MISS"].add(flow)

    def send_miss_flow_to_ovs(self):
        '''
        send missrule flows to io
        '''
        if 0 == len(self._flow_tree["MISS"]):
            return

        self._drv.write_add_flow(self._flow_tree["MISS"])

    def add_identify_flow(self, tenant_id, flow, match_key, action):
        '''
        add identify flow
        :param tenant_id: tenant id
        :param flow: flow string
        :param match: match string
        :param action: action string
        '''
        if not isinstance(match_key, str) or not isinstance(action, str):
            return

        match = "I" + match_key 
        if tenant_id not in self._flow_tree:
            self._flow_tree[tenant_id] = {}
            self._flow_tree[tenant_id]["IDENTIFY"] = {}
            self._flow_tree[tenant_id]["FORWARD"] = {}
            self._flow_tree[tenant_id]["ROUTE"] = {}
            self._flow_tree[tenant_id]["GROUP"] = {}

        if match not in self._flow_tree[tenant_id]["IDENTIFY"]:
            self._log.debug("Identify flow db add:%s" % flow)
            self._flow_tree[tenant_id]["IDENTIFY"][match] = {action: flow}
            self._compare_tree["IDENTIFY"]["ADD"].add(match)
        else:
            if action not in self._flow_tree[tenant_id]["IDENTIFY"][match]:
                self._log.debug("Identify flow db update:%s" % flow)
                self._flow_tree[tenant_id]["IDENTIFY"][match] = {action: flow}
                self._compare_tree["IDENTIFY"]["MOD"].add(match)
            else:
                self._log.debug("Identify flow db exist:%s" % flow)
                self._compare_tree["IDENTIFY"]["EXIST"].add(match)

    def add_l2_flow(self, tenant_id, flow, match_key, action):
        '''
        add forwarding flow
        :param tenant_id: tenant id
        :param flow: flow string
        :param match: match string
        :param action: action string
        '''
        if not isinstance(match_key, str) or not isinstance(action, str):
            return

        match = "F" + match_key 
        if tenant_id not in self._flow_tree:
            self._flow_tree[tenant_id] = {}
            self._flow_tree[tenant_id]["FORWARD"] = {}
            self._flow_tree[tenant_id]["ROUTE"] = {}
            self._flow_tree[tenant_id]["GROUP"] = {}

        if match not in self._flow_tree[tenant_id]["FORWARD"]:
            self._log.debug("L2 flow db add:%s" % flow)
            self._flow_tree[tenant_id]["FORWARD"][match] = {action: flow}
            self._compare_tree["FORWARD"]["ADD"].add(match)
        else:
            if action not in self._flow_tree[tenant_id]["FORWARD"][match]:
                self._log.debug("L2 flow db update:%s" % flow)
                self._flow_tree[tenant_id]["FORWARD"][match] = {action: flow}
                self._compare_tree["FORWARD"]["MOD"].add(match)
            else:
                self._log.debug("L2 flow db exist:%s" % flow)
                self._compare_tree["FORWARD"]["EXIST"].add(match)

    def add_l3_flow(self, tenant_id, flow, match_key, action):
        '''
        add route flow
        :param tenant_id: tenant id
        :param flow: flow string
        :param match: match string
        :param action: action string
        '''
        if not isinstance(match_key, str) or not isinstance(action, str):
            return

        match = "R" + match_key
        if tenant_id not in self._flow_tree:
            self._flow_tree[tenant_id] = {}
            self._flow_tree[tenant_id]["ROUTE"] = {}
            self._flow_tree[tenant_id]["GROUP"] = {}

        if match not in self._flow_tree[tenant_id]["ROUTE"]:
            self._log.debug("L3 flow db add:%s" % flow)
            self._flow_tree[tenant_id]["ROUTE"][match] = {action: flow}
            self._compare_tree["ROUTE"]["ADD"].add(match)
        else:
            if action not in self._flow_tree[tenant_id]["ROUTE"][match]:
                self._log.debug("L3 flow db update:%s" % flow)
                self._flow_tree[tenant_id]["ROUTE"][match] = {action: flow}
                self._compare_tree["ROUTE"]["MOD"].add(match)
            else:
                self._log.debug("L3 flow db exist:%s" % flow)
                self._compare_tree["ROUTE"]["EXIST"].add(match)

    def add_group_flow(self, tenant_id, flow, match_key, action):
        '''
        add route flow
        :param tenant_id: tenant id
        :param flow: flow string
        :param match: match string
        :param action: action string
        '''
        if not isinstance(match_key, str) or not isinstance(action, str):
            return

        match = "G" + match_key
        if tenant_id not in self._flow_tree:
            self._flow_tree[tenant_id] = {}
            self._flow_tree[tenant_id]["GROUP"] = {}

        if match not in self._flow_tree[tenant_id]["GROUP"]:
            self._log.debug("Group flow db add:%s" % flow)
            self._flow_tree[tenant_id]["GROUP"][match] = {action: flow}
            self._compare_tree["GROUP"]["ADD"].add(match)
        else:
            if action not in self._flow_tree[tenant_id]["GROUP"][match]:
                self._log.debug("Group flow db update:%s" % flow)
                self._flow_tree[tenant_id]["GROUP"][match] = {action: flow}
                self._compare_tree["GROUP"]["MOD"].add(match)
            else:
                self._log.debug("Group flow db exist:%s" % flow)
                self._compare_tree["GROUP"]["EXIST"].add(match)

    def add_flows_to_ovs(self, tenant_id):
        '''
        send flows to io
        :param tenant_id: tenant id
        '''
        if tenant_id not in self._flow_tree:
            return

        del_flows = set()
        mod_flows = set()
        add_flows = set()
        del_keys = set()

        # get tenant_id flows in db
        flows = self._flow_tree[tenant_id]

        for key in flows["GROUP"]:
            if key in self._compare_tree["GROUP"]["ADD"]:
                for sub_key in flows["GROUP"][key]:
                    add_flows.add(flows["GROUP"][key][sub_key])
            elif key in self._compare_tree["GROUP"]["MOD"]:
                for sub_key in flows["GROUP"][key]:
                    mod_flows.add(flows["GROUP"][key][sub_key])
            elif key in self._compare_tree["GROUP"]["EXIST"]:
                continue
            else:
                for sub_key in flows["GROUP"][key]:
                    del_flows.add(flows["GROUP"][key][sub_key])
                    del_keys.add(key)

        self._drv.write_add_flow(add_flows, True)
        self._drv.write_mod_flow(mod_flows, True)
        self._drv.write_del_flow(del_flows, True)

        del_flows.clear()
        mod_flows.clear()
        add_flows.clear()

        for key in flows["IDENTIFY"]:
            if key in self._compare_tree["IDENTIFY"]["ADD"]:
                for sub_key in flows["IDENTIFY"][key]:
                    add_flows.add(flows["IDENTIFY"][key][sub_key])
            elif key in self._compare_tree["IDENTIFY"]["MOD"]:
                for sub_key in flows["IDENTIFY"][key]:
                    mod_flows.add(flows["IDENTIFY"][key][sub_key])
            elif key in self._compare_tree["IDENTIFY"]["EXIST"]:
                continue
            else:
                for sub_key in flows["IDENTIFY"][key]:
                    del_flows.add(flows["IDENTIFY"][key][sub_key])
                    del_keys.add(key)

        for key in flows["FORWARD"]:
            if key in self._compare_tree["FORWARD"]["ADD"]:
                for sub_key in flows["FORWARD"][key]:
                    add_flows.add(flows["FORWARD"][key][sub_key])
            elif key in self._compare_tree["FORWARD"]["MOD"]:
                for sub_key in flows["FORWARD"][key]:
                    mod_flows.add(flows["FORWARD"][key][sub_key])
            elif key in self._compare_tree["FORWARD"]["EXIST"]:
                continue
            else:
                for sub_key in flows["FORWARD"][key]:
                    del_flows.add(flows["FORWARD"][key][sub_key])
                    del_keys.add(key)

        for key in flows["ROUTE"]:
            if key in self._compare_tree["ROUTE"]["ADD"]:
                for sub_key in flows["ROUTE"][key]:
                    add_flows.add(flows["ROUTE"][key][sub_key])
            elif key in self._compare_tree["ROUTE"]["MOD"]:
                for sub_key in flows["ROUTE"][key]:
                    mod_flows.add(flows["ROUTE"][key][sub_key])
            elif key in self._compare_tree["ROUTE"]["EXIST"]:
                continue
            else:
                for sub_key in flows["ROUTE"][key]:
                    del_flows.add(flows["ROUTE"][key][sub_key])
                    del_keys.add(key)

        self._drv.write_add_flow(add_flows)
        self._drv.write_mod_flow(mod_flows)
        self._drv.write_del_flow(del_flows)

        # delete flow in db
        for key in del_keys:
            if key in self._flow_tree[tenant_id]["IDENTIFY"]:
                self._flow_tree[tenant_id]["IDENTIFY"].pop(key)
                self._log.debug("Del_key(identify):%s" % key)
            elif key in self._flow_tree[tenant_id]["FORWARD"]:
                self._flow_tree[tenant_id]["FORWARD"].pop(key)
                self._log.debug("Del_key(l2):%s" % key)
            elif key in self._flow_tree[tenant_id]["ROUTE"]:
                self._flow_tree[tenant_id]["ROUTE"].pop(key)
                self._log.debug("Del_key(l3):%s" % key)
            elif key in self._flow_tree[tenant_id]["GROUP"]:
                self._flow_tree[tenant_id]["GROUP"].pop(key)
                self._log.debug("Del_key(group):%s" % key)
            else:
                self._log.debug("Del_key(no name):%s" % key)
                continue

        self._compare_tree_clear()

    def _compare_tree_clear(self):
        '''
        clear the compare tree if complete compare
        '''
        gc = self._compare_tree["IDENTIFY"]["ADD"]
        gc.clear()
        gc = self._compare_tree["IDENTIFY"]["MOD"]
        gc.clear()
        gc = self._compare_tree["IDENTIFY"]["EXIST"]
        gc.clear()

        gc = self._compare_tree["FORWARD"]["ADD"]
        gc.clear()
        gc = self._compare_tree["FORWARD"]["MOD"]
        gc.clear()
        gc = self._compare_tree["FORWARD"]["EXIST"]
        gc.clear()

        gc = self._compare_tree["ROUTE"]["ADD"]
        gc.clear()
        gc = self._compare_tree["ROUTE"]["MOD"]
        gc.clear()
        gc = self._compare_tree["ROUTE"]["EXIST"]
        gc.clear()

        gc = self._compare_tree["GROUP"]["ADD"]
        gc.clear()
        gc = self._compare_tree["GROUP"]["MOD"]
        gc.clear()
        gc = self._compare_tree["GROUP"]["EXIST"]
        gc.clear()
