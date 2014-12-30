import eventlet
eventlet.monkey_patch()
import sys

from oslo.config import cfg
from neutron.common import rpc
from neutron.common import config as common_config
from neutron.agent.common import config
from neutron.agent.linux import interface
from neutron.openstack.common import service
from neutron.clb.agent import manager
from neutron.clb.agent import opts
from neutron.clb.common import topics


class ClbAgentService(service.Service):
    
    def __init__(self):
        super(ClbAgentService, self).__init__()
        self.host = cfg.CONF.host
        self.topic = topics.CLB_AGENT_RPC
        self.manager = manager.ClbAgentManager(cfg.CONF)
        self.conn = rpc.create_connection(new=True)
    
    def start(self):
        super(ClbAgentService, self).start()

        endpoints = [self.manager]
        node_topic = '%s.%s' % (self.topic, self.host)

        self.conn.create_consumer(self.topic, endpoints, fanout=False)
        self.conn.create_consumer(node_topic, endpoints, fanout=False)
        self.conn.create_consumer(self.topic, endpoints, fanout=True)

        self.manager.init()

        self.conn.consume_in_threads()
        
        self.tg.add_timer(
            cfg.CONF.AGENT.periodic_interval,
            self.manager.run_periodic_tasks,
            None,
            None
        )
        
    def stop(self):
        try:
            # in Juno there is not a close method for rpc.Connection class.
            self.conn.close()
        except Exception:
            pass
        super(ClbAgentService, self).stop()


def main():
    opts.register_opts(cfg.CONF)
    # import interface options just in case the driver uses namespaces
    cfg.CONF.register_opts(interface.OPTS)

    common_config.init(sys.argv[1:])
    config.setup_logging()

    service.launch(ClbAgentService()).wait()
