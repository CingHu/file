# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo.config import cfg
from neutron.agent.common import config
from neutron.plugins.centec.agent.ovs_agent.lib.CentecConstants import CentecConstants as CONST


agent_opts = [
    cfg.IntOpt('polling_interval',
               default=2,
               help=_("The number of seconds the agent will wait between "
                      "polling for local device changes.")),
    cfg.BoolOpt('minimize_polling',
                default=True,
                help=_("Minimize polling by monitoring ovsdb for interface "
                       "changes.")),
    cfg.IntOpt('ovsdb_monitor_respawn_interval',
               default=CONST.DEFAULT_OVSDBMON_RESPAWN,
               help=_("The number of seconds to wait before respawning the "
                      "ovsdb monitor after losing communication with it")),
    cfg.StrOpt('integration_bridge',
               default='br-int',
               help=_("Integration bridge to use")),
    cfg.StrOpt('flat_bridge',
               default='br-flat',
               help=_("flat bridge to use")),
    cfg.StrOpt('cloud_manager_ip',
               default="127.0.0.1",
               help=_("The ip address of cloud-manager")),
    cfg.IntOpt('connect_port',
               default=16888,
               help=_("The TCP port to use for connect to cloud-manager")),
    cfg.StrOpt('lldp_interface',
               default='dummy',
               help=_("Interface to use for send LLDP packet")),
    cfg.IntOpt('send_lldp_interval',
               default=10,
               help=_("The number of seconds to Send LLDP packet")),
    cfg.StrOpt('flat_interface',
               default='dummy',
               help=_("Interface to use for support to flat network"))
]

securitygroup_opts = [
    cfg.StrOpt('firewall_driver',
               help=_('Driver for security groups firewall in the L2 agent')),
    cfg.BoolOpt('enable_security_group',
                default=True,
                help=_(
                    'Controls whether the neutron security group API is enabled '
                    'in the server. It should be false when using no security '
                    'groups or using the nova security group API.')),
    cfg.BoolOpt('enable_ipset',
                default=True,
                help=_('Use ipset to speed-up the iptables based security groups.'))
]

cfg.CONF.register_opts(agent_opts, "AGENT")
cfg.CONF.register_opts(securitygroup_opts, "SECURITYGROUP")
config.register_agent_state_opts_helper(cfg.CONF)
config.register_root_helper(cfg.CONF)
