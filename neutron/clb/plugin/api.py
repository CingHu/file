from neutron import manager
from neutron.db import agents_db
from neutron.db import api as neutron_dbapi
from neutron.common import rpc
from neutron.extensions import portbindings
from neutron.openstack.common import log

from neutron.clb.plugin import apibase
from neutron.clb.common import topics
from neutron.clb.common import exceptions
from neutron.clb.plugin import scheduler
from neutron.clb.db import dbapi


LOG = log.getLogger(__name__)


class ClbPluginRpc(rpc.RpcCallback):
    """Plugin side agent-to-plugin callbacks."""
    RPC_API_VERSION = '1.0'

    #########################################################
    # Load balancer operation result notification
    #########################################################

    def __init__(self):
        super(ClbPluginRpc, self).__init__()

    def notify_create_load_balancer_succ(self, context, load_balancer_id):
        dbapi.create_load_balancer_succ(context, load_balancer_id)

    def notify_create_load_balancer_fail(self, context, load_balancer_id):
        dbapi.create_load_balancer_fail(context, load_balancer_id)

    def notify_delete_load_balancer_succ(self, context, load_balancer_id):
        dbapi.delete_load_balancer_succ(context, load_balancer_id)

    def notify_delete_load_balancer_fail(self, context, load_balancer_id):
        dbapi.delete_load_balancer_fail(context, load_balancer_id,
                                        state_error=True)

    def notify_sync_load_balancer_succ(self, context, load_balancer_id):
        dbapi.sync_load_balancer_succ(context, load_balancer_id)

    def notify_sync_load_balancer_fail(self, context, load_balancer_id):
        dbapi.sync_load_balancer_fail(context, load_balancer_id)

    #########################################################
    # Interface operation result notification
    #########################################################

    def notify_create_interface_succ(self, context, interface_id):
        dbapi.create_interface_succ(context, interface_id)
    
    def notify_create_interface_fail(self, context, interface_id):
        dbapi.create_interface_fail(context, interface_id)

    def notify_delete_interface_succ(self, context, interface_id):
        dbapi.delete_interface_succ(context, interface_id)
    
    def notify_delete_interface_fail(self, context, interface_id):
        dbapi.delete_interface_fail(context, interface_id, state_error=True)

    def notify_update_interface_succ(self, context, interface_id):
        dbapi.update_interface_succ(context, interface_id)
    
    def notify_update_interface_fail(self, context, interface_id):
        dbapi.update_interface_fail(context, interface_id, need_update=True)

    def notify_plug_interface_port(self, context, port_id, host):
        core_plugin = manager.NeutronManager.get_plugin()

        port = {
            'admin_state_up': True,
            portbindings.HOST_ID: host
        }        

        core_plugin.update_port(context, port_id, {'port': port})

    def get_all_load_balancers(self, context, host):
        agent_id = scheduler.get_agent_id_by_host(context, host)
        load_balancer_ids = scheduler.get_load_balancer_ids_by_agent(context,
                                                                     agent_id)
        return [dbapi.prepare_load_balancer_for_check(context, 
                                                      load_balancer_id)
                for load_balancer_id in load_balancer_ids]

    def update_backend_health_state(self, context, backend_id, health_state,
                                    updated_at):
        dbapi.update_backend_health_state(context, backend_id, health_state,
                                          updated_at)


class ClbAgentRpcApi(rpc.RpcProxy):
    """Plugin side plugin-to-agent RPC API."""
    BASE_RPC_API_VERSION = '1.1'
    # history
    #   1.0 Initial version
    #   1.1 routes support
    #       - support subnet host-routes
    #       - suppport refresh_routes api

    def __init__(self, topic):
        super(ClbAgentRpcApi, self).__init__(topic, self.BASE_RPC_API_VERSION)

    def _cast(self, agent, context, method, kwargs, version=None):
        return self.cast(
            context,
            self.make_msg(method, **kwargs),
            topic='%s.%s' % (self.topic, agent['host']),
            version=version
        )

    def create_load_balancer(self, agent, context, load_balancer):
        kargs = {'load_balancer': load_balancer} 
        return self._cast(agent, context, 'create_load_balancer', kargs)
    
    def delete_load_balancer(self, agent, context, load_balancer):
        kargs = {'load_balancer': load_balancer}
        return self._cast(agent, context, 'delete_load_balancer', kargs)

    def sync_load_balancer(self, agent, context, load_balancer):
        kargs = {'load_balancer': load_balancer}
        return self._cast(agent, context, 'sync_load_balancer', kargs)

    def create_interface(self, agent, context, load_balancer, interface):
        kargs = {'load_balancer': load_balancer, 'interface': interface}
        return self._cast(agent, context, 'create_interface', kargs)
    
    def delete_interface(self, agent, context, load_balancer, interface):
        kargs = {'load_balancer': load_balancer, 'interface': interface}
        return self._cast(agent, context, 'delete_interface', kargs)

    def update_interface(self, agent, context, load_balancer, interface):
        kargs = {'load_balancer': load_balancer, 'interface': interface}
        return self._cast(agent, context, 'update_interface', kargs)

    def refresh_routes(self, agent, context, load_balancer):
        kargs = {'load_balancer': load_balancer}
        return self.call(agent, context, 'load_balancer', kargs)


class ClbPluginApi(apibase.ClbPluginApiBase):
    """Implementation of the Neutron Chinac Load Balance service plugin."""

    supported_extension_aliases = ['clb']

    def __init__(self):
        # no service type manager support
        self.agent_rpc = ClbAgentRpcApi(topics.CLB_AGENT_RPC)
        self.scheduler = scheduler.ClbAgentScheduler()
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        self.endpoints = [
            ClbPluginRpc(),
            agents_db.AgentExtRpcCallback()
        ]

        self.conn = rpc.create_connection(new=True)
        self.conn.create_consumer(
            topics.CLB_PLUGIN_RPC,
            self.endpoints,
            fanout=False
        )

        self.conn.consume_in_threads()

    ###################################################
    # agent and scheduler operations used inside class
    ###################################################

    def _get_agent(self, context, load_balancer_id):
        # TODO: get_agent_for_load_balancer()
        agent = self.scheduler.get_agent_for_load_balancer(
            context, 
            load_balancer_id
        )
        
        if not agent:
            raise exceptions.NoActiveAgent(load_balancer_id)
        
        return agent
    
    def _schedule(self, context, load_balancer):
        agent = self.scheduler.schedule(context, load_balancer)

        if not agent:
            raise exceptions.NoEligibleAgent(load_balancer['id'])
        
        return agent
        
    ###########################################
    # load balancer operations
    ###########################################
    
    def create_load_balancer(self, context, load_balancer):
        load_balancer = dbapi.create_load_balancer_start(
            context, 
            load_balancer['load_balancer']
        )

        try:
            agent = self._schedule(context, load_balancer)
            self.agent_rpc.create_load_balancer(agent, context, load_balancer)
        except:
            dbapi.create_load_balancer_fail(context, load_balancer['id'])
            msg = "Creating load balancer %s failed"
            LOG.exception(msg % load_balancer['id'])

        return self.get_load_balancer(context, load_balancer['id'])
    
    def update_load_balancer(self, context, load_balancer_id, load_balancer):
        load_balancer = load_balancer['load_balancer']
        return dbapi.update_load_balancer(context, load_balancer_id, 
                                          load_balancer)
    
    def delete_load_balancer(self, context, load_balancer_id):
        LOG.info("Delete load balancer %s" % load_balancer_id)
        load_balancer = dbapi.delete_load_balancer_start(context, 
                                                         load_balancer_id)
    
        try:
            agent = self._get_agent(context, load_balancer_id)
            self.agent_rpc.delete_load_balancer(agent, context, load_balancer)
        except exceptions.NoActiveAgent:
            dbapi.delete_load_balancer_succ(context, load_balancer_id)
        except:
            msg = "Deleting load balancer failed"
            LOG.exception(msg % load_balancer_id)
            dbapi.delete_load_balancer_fail(context, load_balancer_id)

    def get_load_balancer(self, context, load_balancer_id, fields=None):
        return dbapi.get_load_balancer(context, load_balancer_id, 
                                       fields=fields)
    
    def get_load_balancers(self, context, filters=None, fields=None):
        return dbapi.get_load_balancers(context, filters=filters, 
                                        fields=fields)

    def sync_load_balancer(self, context, load_balancer_id):
        load_balancer = dbapi.sync_load_balancer_start(context, 
                                                       load_balancer_id)
        
        try:
            agent = self._get_agent(context, load_balancer_id)
            self.agent_rpc.sync_load_balancer(agent, context, load_balancer)
        except:
            msg = "Syncronization of load balancer %s state faild"
            LOG.exception(msg % load_balancer_id)
            dbapi.sync_load_balancer_fail(context, load_balancer_id)

    def refresh_routes(self, context, load_balancer_id):
        # this is a syncronized api call
        load_balancer = dbapi.prepare_refresh_routes(context, load_balancer_id)
        try:
            agent = self._get_agent(context, load_balancer_id)
            self.agent_rpc.refresh_routes(agent, context, load_balancer)
        except:
            msg = "Refreshing routes of load balancer %(id)s failed"
            LOG.error(msg % load_balancer)

    ########################################
    # interface operations
    ########################################
    
    def create_interface(self, context, interface):
        vif = dbapi.create_interface(context, interface['interface'])

        lb_id = vif['load_balancer_id']
        lb = dbapi.prepare_lb_for_vif_operations(context, lb_id)

        try:
            agent = self._get_agent(context, lb_id)
            self.agent_rpc.create_interface(agent, context, lb, vif)
        except:
            LOG.exception("Creating interface %(id)s failed" % vif)
            dbapi.create_interface_fail(context, vif['id'])
        
        return self.get_interface(context, vif['id'])
    
    def update_interface(self, context, interface_id, interface):
        vif = interface['interface']
        if not vif:
            return self.get_interface(context, interface_id)
        
        attrs = ['subnet_id', 'ip_address', 'inbound_limit', 'outbound_limit']
        call_agent = True if [set(attrs) & set(vif.keys())] else False
        
        if not call_agent:
            return dbapi.update_interface_without_agent(context, interface_id, 
                                                        vif)
        else:
            return self._upadate_interface_with_agent(context, interface_id, 
                                                      vif)

    def _upadate_interface_with_agent(self, context, vif_id, vif):
        vif = dbapi.update_interface_with_agent(context, vif_id, vif)

        lb_id = vif['load_balancer_id']
        lb = dbapi.prepare_lb_for_vif_operations(context, lb_id)
        
        try:
            agent = self._get_agent(context, lb_id)
            self.agent_rpc.update_interface(agent, context, lb, vif)
        except:
            dbapi.update_interface_fail(context, vif_id)
            LOG.exception("Updating interface %(id)s failed, need resync" % vif)
        
        return self.get_interface(context, vif['id'])

    def delete_interface(self, context, interface_id):
        vif = dbapi.delete_interface_start(context, interface_id)

        lb_id = vif['load_balancer_id']
        lb = dbapi.prepare_lb_for_vif_operations(context, lb_id)
        
        try:
            agent = self._get_agent(context, lb_id)
            self.agent_rpc.delete_interface(agent, context, lb, vif)
        except:
            dbapi.delete_interface_fail(context, interface_id)
            LOG.exception("Deleting interface %(id)s failed" % vif)
        
        return dbapi.get_interface(context, interface_id)
    
    def get_interface(self, context, interface_id, fields=None):
        return dbapi.get_interface(context, interface_id, fields=fields)
    
    def get_interfaces(self, context, filters=None, fields=None):
        return dbapi.get_interfaces(context, filters=filters, fields=fields)

    #########################################
    # certificate operations
    #########################################
    
    def create_certificate(self, context, certificate):
        certificate = certificate['certificate']
        return dbapi.create_certificate(context, certificate)
    
    def update_certificate(self, context, certificate_id, certificate):
        certificate = certificate['certificate']
        if certificate:
            return dbapi.update_certificate(context, certificate_id, 
                                            certificate)
        else:
            return self.get_certificate(context, certificate_id)
    
    def delete_certificate(self, context, certificate_id):
        dbapi.delete_certificate(context, certificate_id)
    
    def get_certificate(self, context, certificate_id, fields=None):
        return dbapi.get_certificate(context, certificate_id, fields=fields)
    
    def get_certificates(self, context, filters=None, fields=None):
        return dbapi.get_certificates(context, filters=filters, fields=fields)

    ###########################################
    # listener operations
    ###########################################
    
    def create_listener(self, context, listener):
        listener = listener['listener']
        return dbapi.create_listener(context, listener)
    
    def update_listener(self, context, listener_id, listener):
        listener = listener['listener']
        if listener:
            return dbapi.update_listener(context, listener_id, listener)
        else:
            return self.get_listener(context, listener_id)
    
    def delete_listener(self, context, listener_id):
        dbapi.delete_listener(context, listener_id)
    
    def get_listener(self, context, listener_id, fields=None):
        return dbapi.get_listener(context, listener_id, fields=fields)
    
    def get_listeners(self, context, filters=None, fields=None):
        return dbapi.get_listeners(context, filters=filters, fields=fields)

    ########################################################
    # backend operations
    ########################################################
    
    def create_backend(self, context, backend):
        backend = backend['backend']
        return dbapi.create_backend(context, backend)
    
    def update_backend(self, context, backend_id, backend):
        backend = backend['backend']
        if backend:
            return dbapi.update_backend(context, backend_id, backend)
        else:
            return self.get_backend(context, backend_id)

    def delete_backend(self, context, backend_id):
        dbapi.delete_backend(context, backend_id)
    
    def get_backend(self, context, backend_id, fields=None):
        return dbapi.get_backend(context, backend_id, fields=fields)
    
    def get_backends(self, context, filters=None, fields=None):
        return dbapi.get_backends(context, filters=filters, fields=fields)