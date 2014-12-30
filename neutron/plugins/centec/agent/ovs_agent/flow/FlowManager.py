#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-agent flow module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

from neutron.plugins.centec.agent.ovs_agent.lib.FlowService import FlowService
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


class FlowManager(FlowService):
    def __init__(self, db, host_name, int_br, ofport):
        '''
        init FlowManager
        :param db: database
        :param host_name: host name
        :param ofport: phy port
        '''
        super(FlowManager, self).__init__()
        self._host_name = host_name
        self._db = db
        self._add_missrule_flows()
        self._phy_port = ofport
        self._int_br = int_br

    def calculate_identify_flows(self, subnet_id, local_topo, remote_topo):
        '''
        calculate tanent identify flow table
        :param subnet_id: subnet id
        :param local_topo: {tenant_id:set(my host ports)}
        :param remote_topo: {tenant_id:set(other host ports)}
        '''
        if not isinstance(local_topo, dict):
            self._log.error("Identify local_topo is not a dict")
            return False

        if not isinstance(remote_topo, dict):
            self._log.error("Identify remote_topo is not a dict")
            return False

        # get broadcast id
        state, subnet_info = self._db.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                           subnet_id)
        if state:
            bc_id = subnet_info.get_broadcast_id()
        else:
            self._log.info("Get broadcast_id fail(identify):%s" % subnet_id)
            return False

        is_peer = False
        for tenant_id in local_topo:
            if 0 == len(local_topo[tenant_id]):
                return True

            if 0 != len(remote_topo[tenant_id]):
                # remote host have port
                is_peer = True

            # get vlan
            vlan_id = self._lookup_vlan(tenant_id)
            if not vlan_id:
                self._log.warn("Get vlan_id fail(identify):%s" % tenant_id)
                return False

            # handle vif
            priority = CONST.UNITCAST_PRO
            for port_info in local_topo[tenant_id]:
                mac = port_info.get_mac_addr()
                flow = "table=0,priority=%d,dl_vlan=0xffff,dl_src=%s," % \
                       (priority, mac) + \
                       "actions=mod_vlan_vid:%d,write_metadata:%d,goto_table:1" % \
                       (vlan_id, bc_id)
                match_str = str(mac)
                action_str = str(vlan_id) + str(bc_id)
                # add to flow db
                self.add_identify_flow(tenant_id, flow, match_str, action_str)

            # handle phy_port
            if is_peer:
                for port_info in remote_topo[tenant_id]:
                    mac = port_info.get_mac_addr()
                    flow = "table=0,priority=%d,dl_vlan=%d,dl_src=%s," % \
                           (priority, vlan_id, mac) + \
                           "actions=write_metadata:%d,goto_table:1" % bc_id
                    match_str = str(mac) + str(vlan_id)
                    action_str = str(bc_id)
                    # add to flow db
                    self.add_identify_flow(tenant_id, flow, match_str, action_str)

        return True

    def calculate_normal_flows(self, local_topo, remote_topo):
        '''
        calculate tanent identify flow table to normal
        :param local_topo: {tenant_id:set(my host ports)}
        :param remote_topo: {tenant_id:set(other host ports)}
        '''
        if not isinstance(local_topo, dict):
            self._log.error("Identify local_topo is not a dict")
            return False

        if not isinstance(remote_topo, dict):
            self._log.error("Identify remote_topo is not a dict")
            return False

        for tenant_id in local_topo:
            if 0 == len(local_topo[tenant_id]):
                return True

            # handle vif
            priority = CONST.UNITCAST_PRO
            for port_info in local_topo[tenant_id]:
                port_id = port_info.get_port_id()
                ofport = port_info.get_ofport_id()
                attrs = self._int_br.get_vif_port_by_id(port_id)
                if attrs:
                    port_name = attrs.port_name
                    if attrs.ofport != ofport:
                        self._log.warn("Port:%s, ofport_db:%s, ofport_ovs:%s" %
                                       (port_id, ofport, attrs.ofport))
                        ofport = attrs.ofport

                    self._int_br.set_db_attribute("Port", port_name,
                                                  "tag", CONST.DEFAULT_VLAN)
                    self._log.debug("Port:%s set vlan tag:1" % port_id)
                else:
                    self._log.warn("Port:%s can't find attrs on ovs" % port_id)
                    continue

                flow = "table=0,priority=%d,in_port=%s," % (priority, ofport) + \
                       "actions=normal"
                match_str = str(ofport)
                action_str = "normal"
                # add to flow db
                self.add_identify_flow(tenant_id, flow, match_str, action_str)

        return True

    def calculate_forwarding_flows(self, subnet_id, local_topo, remote_topo):
        '''
        calculate forwarding flow table
        :param subnet_id: subnet id
        :param local_topo: {tenant_id:set(my host ports)}
        :param remote_topo: {tenant_id:set(other host ports)}
        '''
        if not isinstance(local_topo, dict):
            self._log.error("Forwarding local_topo is not dict")
            return False

        if not isinstance(remote_topo, dict):
            self._log.error("Forwarding remote_topo is not dict")
            return False

        is_peer = False
        for tenant_id in local_topo:
            if 0 == len(local_topo[tenant_id]):
                return True

            if 0 != len(remote_topo[tenant_id]):
                # remote host have port
                is_peer = True

            local_ports = local_topo[tenant_id]
            remote_ports = remote_topo[tenant_id]

            # get broadcast id
            state, subnet_info = self._db.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                               subnet_id)
            if state:
                bc_id = subnet_info.get_broadcast_id()
            else:
                self._log.warn("Get broadcast_id fail(forward):%s" % subnet_id)
                return False

            # get vlan
            vlan_id = self._lookup_vlan(tenant_id)
            if not vlan_id:
                self._log.warn("Get vlan_id fail(forward):%s" % tenant_id)
                return False

            # calculate remote flows
            if is_peer:
                for port_info in remote_ports:
                    self._add_flow_in_diff_host(tenant_id, bc_id, vlan_id, port_info)
            # calculate local flows
            for port_info in local_ports:
                self._add_flow_in_same_host(tenant_id, bc_id, vlan_id, port_info)

        return True

    def calculate_broadcast_flows(self, subnet_id, local_topo, remote_topo):
        '''
        calculate broadcast flow table
        :param subnet_id: subnet id
        :param local_topo: dict, {tenant_id:set(my host ports)}
        :param remote_topo: dict, {tenant_id:set(other host ports)}
        '''
        if not isinstance(local_topo, dict):
            self._log.error("Broadcast local_topo is not dict")
            return False

        if not isinstance(remote_topo, dict):
            self._log.error("Broadcast remote_topo is not dict")
            return False

        is_peer = False
        for tenant_id in local_topo:
            if 0 == len(local_topo[tenant_id]):
                return True

            if 0 != len(remote_topo[tenant_id]):
                # remote host have port
                is_peer = True

            local_ports = local_topo[tenant_id]

            # calculate remote flows
            if is_peer:
                self._add_flows_to_broadcast(tenant_id, subnet_id, local_ports, True)
            else:
                self._add_flows_to_broadcast(tenant_id, subnet_id, local_ports, False)

        return True

    def calculate_route_flows(self, tenant_id, local_topo, remote_topo):
        '''
        calculate route flow table
        :param tenant_id: tenant id
        :param local_topo: dict, {subnet_id:set(my host ports),...}
        :param remote_topo: dict, {subnet_id:set(other host ports),...}
        '''
        if not isinstance(local_topo, dict):
            self._log.error("Route local_topo is not dict")
            return False

        if not isinstance(remote_topo, dict):
            self._log.error("Route remote_topo is not dict")
            return False

        if 0 == len(local_topo):
            return True

        # get vlan
        vlan_id = self._lookup_vlan(tenant_id)
        if not vlan_id:
            self._log.warn("Get vlan_id fail(route):%s" % tenant_id)
            return False

        local_routers = set()
        # calculate local route flows
        for subnet_id in local_topo:
            state, subnet_info = self._db.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                               subnet_id)
            if state:
                gateways = subnet_info.get_gateways()
                for router_id in gateways:
                    metadata_id = gateways[router_id]["id"]
                    gateway_mac = gateways[router_id]["mac"]
                    # gateway_ip = gateways[router_id]["ip"]
                    # gateway indentify
                    priority = CONST.GW_PRO
                    flow = "table=1,priority=%d,ip,dl_vlan=%d,dl_dst=%s," % \
                           (priority, vlan_id, gateway_mac) + \
                           "actions=write_metadata:%d,goto_table:2" % metadata_id
                    match_str = str(vlan_id) + str(gateway_mac)
                    action_str = str(metadata_id)
                    # add to flow db
                    self.add_l2_flow(tenant_id, flow, match_str, action_str)
                    # arp proxy
                    # self._add_flows_to_arp(tenant_id, gateway_ip, gateway_mac, vlan_id)
                    self._add_flow_to_route(tenant_id, local_topo[subnet_id],
                                            metadata_id, vlan_id, gateway_mac, True)
                    local_routers.add(router_id)
            else:
                self._log.error("Can't find local subnet info(route):%s" % subnet_id)
                continue

        if 0 == len(local_routers):
            return True

        # calculate remote route flows
        for subnet_id in remote_topo:
            state, subnet_info = self._db.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                               subnet_id)
            if state:
                gateways = subnet_info.get_gateways()
                for router_id in gateways:
                    if router_id not in local_routers:
                        continue

                    metadata_id = gateways[router_id]["id"]
                    gateway_mac = gateways[router_id]["mac"]
                    self._add_flow_to_route(tenant_id, remote_topo[subnet_id],
                                            metadata_id, vlan_id, gateway_mac, False)
            else:
                self._log.error("Can't find remote subnet info(route):%s"
                                % subnet_id)
                continue

        return True

    # interior operate
    def _add_missrule_flows(self):
        '''
        construct miss rule flow
        '''
        priority = CONST.MISSRULE_PRO
        flow = "table=0,priority=%d,actions=drop" % priority
        self.add_miss_flow(flow)

        flow = "table=1,priority=%d,actions=drop" % priority
        self.add_miss_flow(flow)

        flow = "table=2,priority=%d,actions=drop" % priority
        self.add_miss_flow(flow)

        flow = "table=3,priority=%d,actions=drop" % priority
        self.add_miss_flow(flow)

        priority = CONST.BROADCAST_PRO
        # add flow for distinguish broadcast
        flow = "table=1,priority=%d," % priority + \
               "dl_dst=ff:ff:ff:ff:ff:ff,actions=goto_table:3"
        self.add_miss_flow(flow)

        self.del_all_groups()
        self.send_miss_flow_to_ovs()

    def _add_flow_in_same_host(self, tenant_id, broadcast_id, vlan_id, port_info):
        '''
        construct flow in same host
        :param tanent_id: tanent id
        :param broadcast_id: broadcast id
        :param vlan_id: vlan id
        :param port_info: PortMessage Class
        '''
        ofport = port_info.get_ofport_id()
        if not ofport:
            return

        mac = port_info.get_mac_addr()
        priority = CONST.UNITCAST_PRO

        flow = "table=1,priority=%d,metadata=%d,dl_vlan=%d,dl_dst=%s," % \
               (priority, broadcast_id, vlan_id, mac) + \
               "actions=strip_vlan,output:%d" % ofport
        match_str = str(broadcast_id) + str(mac) + str(vlan_id)
        action_str = str(ofport)
        # add to flow db
        self.add_l2_flow(tenant_id, flow, match_str, action_str)

        return True

    def _add_flow_in_diff_host(self, tenant_id, broadcast_id, vlan_id, port_info):
        '''
        construct flow in diff host
        :param tanent_id: tanent id
        :param broadcast_id: broadcast id
        :param vlan_id: vlan id
        :param port_info: PortMessage Class
        '''
        mac = port_info.get_mac_addr()
        priority = CONST.UNITCAST_PRO

        flow = "table=1,priority=%d,metadata=%d,dl_vlan=%d,dl_dst=%s," % \
               (priority, broadcast_id, vlan_id, mac) + \
               "actions=output:%s" % self._phy_port
        match_str = str(broadcast_id) + str(mac) + str(vlan_id)
        action_str = str(self._phy_port)
        # add to flow db
        self.add_l2_flow(tenant_id, flow, match_str, action_str)

        return True

    def _add_flow_to_route(self, tenant_id, ports, metadata_id, vlan_id, gateway_mac, is_local):
        '''
        construct route flow
        :param tanent_id: tanent id
        :param ports: prot set()
        :param metadata_id: metadata id
        :param vlan_id: vlan id
        :param gateway_mac: gateway mac
        :param is_local: is local host port
        '''
        router_if = []
        priority = CONST.UNITCAST_PRO
        router_mac = str(gateway_mac)
        router_mac = router_mac[1:]
        router_mac = "e" + router_mac

        if is_local:
            flow = "table=0,priority=%d,dl_vlan=%d,dl_src=%s," % \
                   (priority, vlan_id, router_mac) + \
                   "actions=write_metadata:%d,goto_table:2" % metadata_id
            self._log.debug("-----------identify:%s" % flow)
            match_str = str(router_mac) + str(vlan_id)
            action_str = str(metadata_id)
            # add to flow db
            self.add_identify_flow(tenant_id, flow, match_str, action_str)

            for port_info in ports:
                port_ip = port_info.get_ip_addr()
                port_mac = port_info.get_mac_addr()

                ofport = port_info.get_ofport_id()
                if not ofport:
                    continue
                if port_info.get_device_owner() == CONST.IF_ROUTER:
                    router_if.append(ofport)

                flow = "table=2,priority=%d,metadata=%d," % (priority, metadata_id) + \
                       "ip,nw_dst=%s,dl_vlan=%d," % (port_ip, vlan_id) + \
                       "actions=strip_vlan,set_field:%s->dl_dst,output:%d" % \
                       (port_mac, ofport)
                match_str = str(metadata_id) + str(port_ip)
                action_str = str(port_mac) + str(ofport)
                self.add_l3_flow(tenant_id, flow, match_str, action_str)

            if 0 != len(router_if):
                flow = "table=2,priority=%d,metadata=%d," % (CONST.DEF_ROUTE_PRO, metadata_id) + \
                       "dl_dst=%s,ip,dl_vlan=%d," % (gateway_mac, vlan_id) + \
                       "actions=strip_vlan,output:%s" % (min(router_if))
                match_str = str(metadata_id) + str(gateway_mac) + str(vlan_id)
                action_str = str(router_if[0])
                self.add_l3_flow(tenant_id, flow, match_str, action_str)
            else:
                flow = "table=2,priority=%d,metadata=%d," % (CONST.DEF_ROUTE_PRO, metadata_id) + \
                       "dl_dst=%s,ip,dl_vlan=%d," % (gateway_mac, vlan_id) + \
                       "actions=set_field:%s->dl_src,output:%s" % (router_mac, self._phy_port)
                match_str = str(metadata_id) + str(gateway_mac) + str(vlan_id)
                action_str = str(self._phy_port) + str(router_mac)
                self.add_l3_flow(tenant_id, flow, match_str, action_str)

        else:
            for port_info in ports:
                port_ip = port_info.get_ip_addr()
                port_mac = port_info.get_mac_addr()

                flow = "table=2,priority=%d,metadata=%d," % (priority, metadata_id) + \
                       "ip,nw_dst=%s,actions=set_field:%s->dl_src,set_field:%s->dl_dst,output:%s" % \
                       (port_ip, router_mac, port_mac, self._phy_port)
                match_str = str(metadata_id) + str(port_ip)
                action_str = str(port_mac) + str(self._phy_port) + str(router_mac)
                self.add_l3_flow(tenant_id, flow, match_str, action_str)

        return True

    def _add_flows_to_arp(self, tenant_id, gateway_ip, gateway_mac, vlan_id):
        '''
        construct arp proxy
        :param tenant_id: tenant id
        :param gateway_ip: gateway ip
        :param gateway_mac: gateway mac
        :param vlan_id: vlan id
        '''
        priority = CONST.ARP_PRO
        flow = "table=1,priority=%d,dl_vlan=%d," % (priority, vlan_id) + \
               "dl_type=0x0806,nw_dst=%s," % gateway_ip + \
               "actions=strip_vlan,move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[]," + \
               "set_field:%s->dl_src,set_field:2->arp_op," % gateway_mac + \
               "move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[]," + \
               "set_field:%s->arp_sha," % gateway_mac + \
               "move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[]," + \
               "set_field:%s->arp_spa,in_port" % gateway_ip
        match_str = str(vlan_id) + str(gateway_ip)
        action_str = str(gateway_mac)
        # add to flow db
        self.add_l2_flow(tenant_id, flow, match_str, action_str)

    def _add_flows_to_broadcast(self, tenant_id, subnet_id, local_ports, is_remote):
        '''
        construct broadcast flow
        :param tenant_id: tenant id
        :param subnet_id: subnet id
        :param local_ports: local ports set()
        :param is_remote: whether have remote ports
        '''
        state, subnet_info = self._db.lookup_entry_from_db(CONST.DBTABLE_SUBNET,
                                                           subnet_id)
        if state:
            bc_id = subnet_info.get_broadcast_id()
        else:
            return False

        # get vlan
        vlan_id = self._lookup_vlan(tenant_id)
        if not vlan_id:
            self._log.warn("Get vlan_id fail(broadcast):%s" % tenant_id)
            return False

        # ofport to string
        ofports = set()
        for port_info in local_ports:
            if not port_info.get_ofport_id():
                self._log.warn("Get ofport fail(broadcast):%s" % port_info.get_port_id())
                continue
            ofports.add(str(port_info.get_ofport_id()))

        self._log.debug(ofports)

        priority = CONST.BROADCAST_PRO
        # if only one port, no need to add broadcast flow
        if not is_remote:
            if 2 > len(ofports):
                self._log.debug("No need to add broadcast flow(broadcast):%s" % subnet_id)
                return True

        # add broadcast flow
        flow = "table=3,priority=%d," % priority + \
               "metadata=%d,actions=group:%d" % (bc_id, bc_id)
        match_str = str(bc_id)
        action_str = str(bc_id)
        self.add_identify_flow(tenant_id, flow, match_str, action_str)

        if is_remote:
            phy_port = "bucket=output:%s,bucket=strip_vlan,output:" % self._phy_port
            if 1 == len(ofports):
                for port_id in ofports:
                    vif_port = port_id
                    key = port_id + self._phy_port
            else:
                vif_port = ',bucket=strip_vlan,output:'.join(ofports)
                key = '-'.join(ofports) + self._phy_port

            # group flow
            flow = "group_id=%d," % (bc_id) + \
                   "type=all," + phy_port + vif_port
            match_str = str(bc_id)
            action_str = str(key)
            # add to flow db
            self.add_group_flow(tenant_id, flow, match_str, action_str)
        else:
            vif_port = ',bucket=strip_vlan,output:'.join(ofports)
            key = '-'.join(ofports)

            # group flow
            flow = "group_id=%d," % (bc_id) + \
                   "type=all,bucket=strip_vlan,output:" + vif_port
            match_str = str(bc_id)
            action_str = str(key)
            # add to flow db
            self.add_group_flow(tenant_id, flow, match_str, action_str)

        return True

    def _lookup_vlan(self, tenant_id):
        '''
        lookup vlan
        :param tenant_id: tenant id
        '''
        vlans = self._db.lookup_table_from_db(CONST.DBTABLE_VLAN)
        if 0 == len(vlans):
            return None

        state, host_info = self._db.lookup_entry_from_db(CONST.DBTABLE_HOST,
                                                         self._host_name)
        if state:
            key = host_info.get_tor_id() + "|" + tenant_id
            if key in vlans:
                return vlans[key].get_vlan_id()

        return None
