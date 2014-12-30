# Copyright 2014 OpenStack Foundation
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

import sys

import eventlet
eventlet.monkey_patch()

from oslo.config import cfg

from neutron.agent.common import config
from neutron.agent.linux import ovs_lib
from neutron.agent import rpc as agent_rpc
from neutron.common import config as common_config
from neutron.common import constants as constants
from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron import context
from neutron import manager
from neutron.openstack.common import log as logging
from neutron.openstack.common import loopingcall
from neutron.openstack.common import service
from neutron import service as neutron_service
from neutron.services.qos.agents import qos_rpc


LOG = logging.getLogger(__name__)


class QoSPluginRpc(n_rpc.RpcProxy):

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self):
        super(QoSPluginRpc,
              self).__init__(topic=topics.QOS_AGENT,
                             default_version=self.BASE_RPC_API_VERSION)

class QoSPluginApi(agent_rpc.PluginApi, qos_rpc.QoSServerRpcApiMixin):
    pass

class QoSAgent(QoSPluginRpc, qos_rpc.QoSAgentRpcMixin, manager.Manager):

    QoSOpts = [
        cfg.StrOpt(
            'qos_driver',
            default='neutron.services.qos.drivers.qos_base.NoOpQoSDriver')
    ]

    def __init__(self, host, conf=None):
        self.conf = conf or cfg.CONF
        self.root_helper = config.get_root_helper(self.conf)
        self.context = context.get_admin_context_without_session()
        self.plugin_rpc = QoSPluginApi(topics.PLUGIN)

        self.host = host
        super(QoSAgent, self).__init__()

        br_name = ovs_lib.get_bridges(self.root_helper)[0]
        ext_bridge = ovs_lib.OVSBridge(br_name, self.root_helper)
        self.init_qos(ext_bridge=ext_bridge)


class QoSAgentWithStateReport(QoSAgent):

    def __init__(self, host, conf=None):
        super(QoSAgentWithStateReport, self).__init__(host=host,
                                                      conf=conf)
        self.state_rpc = agent_rpc.PluginReportStateAPI(topics.PLUGIN)
        self.agent_state = {
            'binary': 'neutron-qos-agent',
            'host': host,
            'topic': topics.QOS_AGENT,
            'configurations': {
                'qos_driver': self.conf.qos_driver,
                'report_interval': cfg.CONF.AGENT.report_interval
            },
            'start_flag': True,
            'agent_type': constants.AGENT_TYPE_QOS}
        report_interval = cfg.CONF.AGENT.report_interval
        self.use_call = True
        if report_interval:
            self.heartbeat = loopingcall.FixedIntervalLoopingCall(
                self._report_state)
            self.heartbeat.start(interval=report_interval)

    def _report_state(self):
        try:
            self.state_rpc.report_state(self.context, self.agent_state,
                                        self.use_call)
            self.agent_state.pop('start_flag', None)
            self.use_call = False
        except AttributeError:
            # This means the server does not support report_state
            LOG.warn(_("Neutron server does not support state report."
                       " State report for this agent will be disabled."))
            self.heartbeat.stop()
            return
        except Exception:
            LOG.exception(_("Failed reporting state!"))

    def agent_updated(self, context, payload):
        LOG.info(_("agent_updated by server side %s!"), payload)

def main():
    conf = cfg.CONF
    config.register_agent_state_opts_helper(conf)
    config.register_root_helper(conf)
    common_config.init(sys.argv[1:])
    config.setup_logging()
    server = neutron_service.Service.create(
        binary='neutron-qos-agent',
        topic=topics.QOS_AGENT,
        report_interval=cfg.CONF.AGENT.report_interval,
        manager='neutron.services.qos.agents.'
                'qos_agent.QoSAgentWithStateReport')
    service.launch(server).wait()
