#!/usr/bin/env python
# encoding: utf-8
'''
Copyright 2014 Centec Networks Inc. All rights reserved.

@summary:      ovs-=agent lldp module
@author:       weizj
@organization: Centec Networks
@copyright:    2014 Centec Networks Inc. All rights reserved.
'''

import traceback

from neutron.plugins.centec.agent.ovs_agent.logger.Logger import Logger
from oslo.config import cfg
from neutron.plugins.centec.agent.lldp.lldp_server import LldpServer
from neutron.openstack.common import loopingcall


class LldpManager(object):
    def __init__(self):
        '''
        init
        '''
        self._log = Logger("ovs_agent.lldp")
        self._phy_port = cfg.CONF.AGENT.lldp_interface
        self._time_interval = cfg.CONF.AGENT.send_lldp_interval
        self._root_helper = cfg.CONF.AGENT.root_helper
        self._lldp_server = LldpServer(self._phy_port, self._root_helper)
        self._start_send_lldp_timer()

    def _start_send_lldp_timer(self):
        '''
        lldp send timer
        '''
        send_lldp_timer = loopingcall.FixedIntervalLoopingCall(self._send_lldp)
        send_lldp_timer.start(interval=self._time_interval)

    # sending lldp message to connected tor switch.
    def _send_lldp(self):
        '''
        send lldp packet
        '''
        try:
            self._lldp_server.send_packet()
            self._log.debug("Ovs agent send lldp..!")
        except:
            self._log.error("Please check lldp send interface/interval whether correct")
            self._log.debug(traceback.format_exc())
