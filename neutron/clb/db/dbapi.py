from sqlalchemy import sql
from sqlalchemy.orm.exc import NoResultFound

from neutron import manager
from neutron.common import exceptions as neutron_exc
from neutron.api.v2 import attributes
from neutron.db import sqlalchemyutils
from neutron.openstack.common import uuidutils
from neutron.openstack.common import log
from neutron.openstack.common import timeutils
from neutron.clb.common import constants
from neutron.clb.common import exceptions
from neutron.clb.db import models


LOG = log.getLogger(__name__)


########################################
# basic database api
########################################

_model_query_hooks = {}


def _model_query(context, model):
    query = context.session.query(model)
    # define basic filter condition for model query
    # NOTE(jkoelker) non-admin queries are scoped to their tenant_id
    # NOTE(salvatore-orlando): unless the model allows for shared objects
    query_filter = None
    if not context.is_admin and hasattr(model, 'tenant_id'):
        if hasattr(model, 'shared'):
            query_filter = ((model.tenant_id == context.tenant_id) |
                            (model.shared == sql.true()))
        else:
            query_filter = (model.tenant_id == context.tenant_id)

    # Execute query hooks registered from mixins and plugins
    for _name, hooks in _model_query_hooks.get(model, {}).iteritems():
        query_hook = hooks.get('query')
        if isinstance(query_hook, basestring):
            # TODO: fixme
            # query_hook = getattr(self, query_hook, None)
            pass
        if query_hook:
            query = query_hook(context, model, query)

        filter_hook = hooks.get('filter')
        if isinstance(filter_hook, basestring):
            # TODO: fixme
            # filter_hook = getattr(self, filter_hook, None)
            pass
        if filter_hook:
            query_filter = filter_hook(context, model, query_filter)

    # NOTE(salvatore-orlando): 'if query_filter' will try to evaluate the
    # condition, raising an exception
    if query_filter is not None:
        query = query.filter(query_filter)
    return query


def _get_by_id(context, model, resource_id):
    query = _model_query(context, model)
    return query.filter(model.id == resource_id).one()


def get_resource(context, model, resource_id):
    try:
        resource_db = _get_by_id(context, model, resource_id)
    except NoResultFound:
        if issubclass(model, models.LoadBalancer):
            raise exceptions.LoadBalancerNotFound(resource_id)
        elif issubclass(model, models.Interface):
            raise exceptions.InterfaceNotFound(resource_id)
        elif issubclass(model, models.Backend):
            raise exceptions.BackendNotFound(resource_id)
        elif issubclass(model, models.Listener):
            raise exceptions.ListenerNotFound(resource_id)
        elif issubclass(model, models.ClbCertificate):
            raise exceptions.ListenerNotFound(resource_id)
        else:
            raise
    return resource_db


def _apply_filters_to_query(query, model, filters):
    if filters:
        for key, value in filters.iteritems():
            column = getattr(model, key, None)
            if column:
                query = query.filter(column.in_(value))
        for _name, hooks in _model_query_hooks.get(model, {}).iteritems():
            result_filter = hooks.get('result_filters', None)
            if isinstance(result_filter, basestring):
                # TODO: fixme
                # result_filter = getattr(self, result_filter, None)
                pass
            if result_filter:
                query = result_filter(query, filters)
    return query


def _get_collection_query(context, model, filters=None,
                          sorts=None, limit=None, marker_obj=None,
                          page_reverse=False):
    collection = _model_query(context, model)
    collection = _apply_filters_to_query(collection, model, filters)
    if limit and page_reverse and sorts:
        sorts = [(s[0], not s[1]) for s in sorts]
    collection = sqlalchemyutils.paginate_query(
        collection, model, limit, sorts,
        marker_obj=marker_obj
    )
    return collection


def get_resources(context, model, filters=None, fields=None, 
                  sorts=None, limit=None, marker_obj=None, 
                  page_reverse=False):
    query = _get_collection_query(
        context, 
        model, 
        filters=filters,
        sorts=sorts,
        limit=limit,
        marker_obj=marker_obj,
        page_reverse=page_reverse
    )
    
    items = [resource_db.dict(fields=fields) 
             for resource_db in query]

    if limit and page_reverse:
        items.reverse()

    return items


def get_tenant_id_for_create(context, resource):
        if context.is_admin and 'tenant_id' in resource:
            tenant_id = resource['tenant_id']
        elif ('tenant_id' in resource and
              resource['tenant_id'] != context.tenant_id):
            msg = "Cannot create resource for another tenant"
            raise exceptions.AdminRequired(msg)
        else:
            tenant_id = context.tenant_id
        return tenant_id


#################################################
# Load balancer: Create
#################################################

def create_load_balancer_start(context, load_balancer):
    tenant_id = get_tenant_id_for_create(context, load_balancer)
    with context.session.begin(subtransactions=True):
        load_balancer_db = models.LoadBalancer(
            id=uuidutils.generate_uuid(),
            tenant_id=tenant_id,
            state=constants.STATE_INVALID,
            task_state=constants.TASK_CREATING,
            name=load_balancer.get('name'),
            description=load_balancer.get('description'),
            provider=load_balancer['provider'],
            maxconn=load_balancer['maxconn']
        )
        context.session.add(load_balancer_db)
    
    return load_balancer_db.dict()


def create_load_balancer_succ(context, load_balancer_id):
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    load_balancer_id)
    with context.session.begin(subtransactions=True):
        load_balancer_db.state = constants.STATE_NONE
        load_balancer_db.task_state = constants.TASK_NONE


def create_load_balancer_fail(context, load_balancer_id):
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    load_balancer_id)
    with context.session.begin(subtransactions=True):
        load_balancer_db.state = constants.STATE_ERROR
        load_balancer_db.task_state = constants.TASK_NONE


#################################################
# Load balancer: Delete
#################################################

def _delete_load_balancer_check(load_balancer_db):
    if load_balancer_db.interfaces:
        msg = "Load balancer %s has interfaces attached"
        raise exceptions.ClbException(msg % load_balancer_db.id)

    if load_balancer_db.task_state != constants.TASK_NONE:
        msg = "Load balancer is in task %s"
        raise exceptions.ClbException(msg % load_balancer_db.task_state)

    
def delete_load_balancer_start(context, load_balancer_id):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)

    _delete_load_balancer_check(load_balancer_db)

    with context.session.begin(subtransactions=True):
        load_balancer_db.task_state = constants.TASK_DELETING

    return load_balancer_db.dict()


def delete_load_balancer_succ(context, load_balancer_id):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)

    with context.session.begin(subtransactions=True):
        # remove all listeners & backends
        for listener_db in load_balancer_db.listeners:
            for backend_db in listener_db.backends:
                context.session.delete(backend_db)
            context.session.delete(listener_db)

        # remove all certificates
        for certificate_db in load_balancer_db.certificates:
            context.session.delete(certificate_db)

        context.session.delete(load_balancer_db)


def delete_load_balancer_fail(context, load_balancer_id, state_error=False):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)

    with context.session.begin(subtransactions=True):
        if state_error:
            load_balancer_db.state = constants.STATE_ERROR

        load_balancer_db.task_state = constants.TASK_NONE    


#################################################
# Load balancer: Update
#################################################


def _update_load_balancer_check(load_balancer_db, load_balancer):
    if 'state' in load_balancer or 'task_state' in load_balancer:
        msg = "Load balancer state or task changing not allowed"
        raise exceptions.ClbException(msg)
    
    if load_balancer_db.task_state != constants.TASK_NONE:
        msg = "Load balancer is in task %s"
        raise exceptions.ClbException(msg % load_balancer_db.task_state)
    
    if (load_balancer_db.state != constants.STATE_NONE and
        load_balancer_db.state != constants.STATE_SYNC):
        msg = "Load balancer state is %s"
        raise exceptions.ClbException(msg % load_balancer_db.state)


def update_load_balancer(context, load_balancer_id, load_balancer):
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    load_balancer_id)
    need_sync = False
    if 'maxconn' in load_balancer and load_balancer_db.listeners:
        need_sync = True

    if need_sync:
        _update_load_balancer_check(load_balancer_db, load_balancer)

    with context.session.begin(subtransactions=True):
        load_balancer_db.update(load_balancer)
        if need_sync:
            load_balancer_db.state = constants.STATE_SYNC

    return load_balancer_db.dict()


#################################################
# Load balancer: Retrieve
#################################################


def get_load_balancer(context, load_balancer_id, fields=None):
    load_balancer_db = get_resource(context, models.LoadBalancer,
                                    load_balancer_id)
    return load_balancer_db.dict(fields=fields)


def get_load_balancers(context, filters=None, fields=None):
    return get_resources(context, models.LoadBalancer, filters=filters,
                         fields=fields)


#################################################
# Load balancer: Syncronize
#################################################


def prepare_lb_for_vif_operations(context, lb_id):
    lb_db = get_resource(context, models.LoadBalancer, lb_id)
    vifs = [_prepare_interface_info(context, vif_db)
            for vif_db in lb_db.interfaces]

    lb = lb_db.dict()
    lb['interfaces'] = vifs

    return lb


def prepare_load_balancer_for_check(context, load_balancer_id):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)

    load_balancer = _prepare_load_balancer(load_balancer_db)
    
    interfaces = [_prepare_interface_info(context, interface_db)
                  for interface_db in load_balancer_db.interfaces]
    
    load_balancer['interfaces'] = interfaces
    
    return load_balancer
    

def _prepare_load_balancer(load_balancer_db):
    """Prepare load balancer data for to-agent RPC call."""
    load_balancer = load_balancer_db.dict()
    
    listeners = []
    for listener_db in load_balancer_db.listeners:
        listener = listener_db.dict()
        listener['backends'] = [backend_db.dict()
                                for backend_db 
                                in listener_db.backends]
        listeners.append(listener)
    load_balancer['listeners'] = listeners
    
    certificates = [certificate_db.dict()
                    for certificate_db
                    in load_balancer_db.certificates]
    load_balancer['certificates'] = certificates

    return load_balancer


def prepare_refresh_routes(context, lb_id):
    lb_db = get_resource(context, models.LoadBalancer, lb_id)

    if lb_db.task_state != constants.TASK_NONE:
        msg = "Load balancer is in task %s"
        raise exceptions.ClbException(msg % lb_db.task_state)

    if lb_db.state != constants.STATE_NONE:
        msg = "Load balancer is in state %s"
        raise exceptions.ClbException(msg % lb_db.state)

    return prepare_lb_for_vif_operations(context, lb_id)


def _sync_load_balancer_check(load_balancer_db):
    if load_balancer_db.task_state != constants.TASK_NONE:
        msg = "Load balancer is in task %s"
        raise exceptions.ClbException(msg % load_balancer_db.task_state)
    
    if (load_balancer_db.state != constants.STATE_NONE and
        load_balancer_db.state != constants.STATE_SYNC):
        msg = "Load balancer state is %s"
        raise exceptions.ClbException(msg % load_balancer_db.state)


def sync_load_balancer_start(context, load_balancer_id):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)

    _sync_load_balancer_check(load_balancer_db)

    with context.session.begin(subtransactions=True):
        load_balancer_db.task_state = constants.TASK_SYNCRONIZING

    load_balancer = _prepare_load_balancer(load_balancer_db)
    return load_balancer


def sync_load_balancer_succ(context, load_balancer_id):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)
    with context.session.begin(subtransactions=True):
        load_balancer_db.state = constants.STATE_NONE
        load_balancer_db.task_state = constants.TASK_NONE    


def sync_load_balancer_fail(context, load_balancer_id):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    load_balancer_id)
    with context.session.begin(subtransactions=True):
        load_balancer_db.state = constants.STATE_SYNC
        load_balancer_db.task_state = constants.TASK_NONE    


#################################################
# Interface: update
#################################################


def _prepare_interface_info(context, interface_db):
    interface = interface_db.dict()

    if interface_db.port_id:
        core_plugin = manager.NeutronManager.get_plugin()
        port = core_plugin.get_port(context, interface_db.port_id)
        for fixed_ip in port['fixed_ips']:
            fixed_ip['subnet'] = core_plugin.get_subnet(
                context, fixed_ip['subnet_id']
            )
        interface['port'] = port

    return interface


def _create_interface_port(context, interface_id, interface):
    core_plugin = manager.NeutronManager.get_plugin()
    
    subnet = core_plugin.get_subnet(context, interface['subnet_id'])

    fixed_ip = {
       'subnet_id': interface['subnet_id'],
    }
    
    if interface['ip_address'] is not attributes.ATTR_NOT_SPECIFIED:
        fixed_ip['ip_address'] = interface['ip_address']

    # NOTE(zcq): we can call core_plugin.create_port directly with
    # mac_address == attributes.ATTR_NOT_SPECIFIED

    port = {
        'tenant_id': interface['tenant_id'],
        'name': 'clb-vif-%s' % interface_id,
        'network_id': subnet['network_id'],
        'mac_address': interface['mac_address'],
        'admin_state_up': False,
        'device_id': interface_id,
        'device_owner': 'network:LOADBALANCER',
        'fixed_ips': [fixed_ip] 
    }
    
    port = core_plugin.create_port(context, {'port': port})
    
    return port['id']
    

def _create_interface_check(context, interface):
    load_balancer_id = interface['load_balancer_id']
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    load_balancer_id)
    
    if (load_balancer_db.state == constants.STATE_INVALID or
        load_balancer_db.state == constants.STATE_ERROR):
        msg = "Load balancer %s state is invalid"
        raise exceptions.ClbException(msg % load_balancer_id)
    
    if (load_balancer_db.task_state == constants.TASK_CREATING or
        load_balancer_db.task_state == constants.TASK_DELETING):
        msg = "Load balancer %s task state is invalid"
        raise exceptions.ClbException(msg % load_balancer_id)
    

def create_interface(context, interface):
    _create_interface_check(context, interface)

    tenant_id = get_tenant_id_for_create(context, interface)
    
    with context.session.begin(subtransactions=True):
        interface_db = models.Interface(
            id=uuidutils.generate_uuid(),
            tenant_id=tenant_id,
            state=constants.STATE_INVALID,
            task_state=constants.TASK_CREATING,
            enabled=True,
            is_public=interface['is_public'],
            load_balancer_id=interface['load_balancer_id'],
            inbound_limit = interface['inbound_limit'],
            outbound_limit = interface['outbound_limit']
        )
        
        interface_db.port_id = _create_interface_port(context, 
                                                      interface_db.id, 
                                                      interface)
        context.session.add(interface_db)
    
    return _prepare_interface_info(context, interface_db)


def create_interface_fail(context, interface_id):
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        interface_db.state = constants.STATE_ERROR
        interface_db.task_state = constants.TASK_NONE


def create_interface_succ(context, interface_id):
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        interface_db.state = constants.STATE_NONE
        interface_db.task_state = constants.TASK_NONE


#################################################
# Interface: update
#################################################


def update_interface_without_agent(context, interface_id, interface):
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        interface_db.update(interface)
    return interface_db.dict()


def _update_interface_port(context, port_id, interface):
    core_plugin = manager.NeutronManager.get_plugin()
    port = core_plugin.get_port(context, port_id)
    
    if 'subnet' in interface:
        subnet_id = interface['subnet']
    else:
        # Get first subnet_id
        subnet_id = port['fixed_ips'][0]['subnet_id']
    
    subnet = core_plugin.get_subnet(context, subnet_id)

    fixed_ip = {
        'subnet_id': subnet_id,
        'ip_address': interface['ip_address']
    }

    port = {
        'network_id': subnet['network_id'],
        'fixed_ips': [fixed_ip] 
    }
    
    core_plugin.update_port(context, port_id, {'port': port})


def _update_interface_with_agent_check(context, interface_db, interface):
    load_balancer_id = interface_db.load_balancer_id
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    load_balancer_id)
    
    if (load_balancer_db.state == constants.STATE_INVALID or
        load_balancer_db.state == constants.STATE_ERROR):
        msg = "Load balancer %s state is invalid"
        raise exceptions.ClbException(msg % load_balancer_id)
    
    if (load_balancer_db.task_state == constants.TASK_CREATING or
        load_balancer_db.task_state == constants.TASK_DELETING):
        msg = "Load balancer %s task state is invalid"
        raise exceptions.ClbException(msg % load_balancer_id)

    if (interface_db.state != constants.STATE_NONE and
        interface_db.state != constants.STATE_UPDATE):
        msg = "Interface %s state is invalid"
        raise exceptions.ClbException(msg % interface_db.id)
    
    if interface_db.task_state != constants.TASK_NONE:
        msg = "Interface %s task state is invalid"
        raise exceptions.ClbException(msg % interface_db.id)

    if 'state' in interface or 'task_state' in interface:
        msg = "Interface state or task state changing not allowed"
        raise exceptions.ClbException(msg)

    if 'subnet_id' in interface and 'ip_address' not in interface:
        msg = "ip_address must be provided with subnet_id"
        raise exceptions.ClbException(msg)


def update_interface_with_agent(context, interface_id, interface):
    interface_db = get_resource(context, models.Interface, interface_id)

    _update_interface_with_agent_check(context, interface_db, interface)

    with context.session.begin(subtransactions=True):
        if 'ip_address' in interface:
            _update_interface_port(context, interface_db.port_id, interface)
        interface_db.update(interface)
        interface_db.task_state = constants.TASK_UPDATING
    
    return _prepare_interface_info(context, interface_db)


def update_interface_succ(context, interface_id):    
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        interface_db.state = constants.STATE_NONE
        interface_db.task_state = constants.TASK_NONE 


def update_interface_fail(context, interface_id, need_update=False):
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        if need_update:
            interface_db.state = constants.STATE_UPDATE
        interface_db.task_state = constants.TASK_NONE    


#################################################
# Interface: Delete
#################################################


def _delete_interface_check(context, interface_db):
    # NO CHECK for load balancer state & task_state
    if interface_db.task_state != constants.TASK_NONE:
        msg = "Interface %s task state is invalid"
        raise exceptions.ClbException(msg % interface_db.id)


def delete_interface_start(context, interface_id):
    interface_db = get_resource(context, models.Interface, interface_id)

    _delete_interface_check(context, interface_db)    
    with context.session.begin(subtransactions=True):
        interface_db.task_state = constants.TASK_DELETING
    
    return _prepare_interface_info(context, interface_db)


def delete_interface_fail(context, interface_id, state_error=False):
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        if state_error:
            interface_db.state = constants.STATE_ERROR
        interface_db.task_state = constants.TASK_NONE


def delete_interface_succ(context, interface_id):
    interface_db = get_resource(context, models.Interface, interface_id)
    with context.session.begin(subtransactions=True):
        context.session.delete(interface_db)
        if interface_db.port:
            core_plugin = manager.NeutronManager.get_plugin()
            core_plugin.delete_port(context, interface_db.port_id)


#################################################
# Interface: Retrieve
#################################################


def get_interface(context, interface_id, fields=None):
    interface_db = get_resource(context, models.Interface, interface_id)
    return interface_db.dict(fields=fields)


def get_interfaces(context, filters=None, fields=None):
    return get_resources(context, models.Interface, filters=filters, 
                         fields=fields)


#################################################
# Certificate: CRUD
#################################################
    

def create_certificate(context, certificate):
    load_balancer_id = certificate['load_balancer_id']
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    load_balancer_id)
    
    tenant_id = get_tenant_id_for_create(context, certificate)

    with context.session.begin(subtransactions=True):
        certificate_db = models.ClbCertificate(
            id=uuidutils.generate_uuid(),
            tenant_id=tenant_id,
            name=certificate.get('name'),
            description=certificate.get('description'),
            certificate=certificate['certificate'],
            key=certificate['key'],
            load_balancer_id=load_balancer_id
        )

        context.session.add(certificate_db)
    
    return certificate_db.dict()


def _update_certificate_check(load_balancer_db):
    if (load_balancer_db.state != constants.STATE_NONE and
        load_balancer_db.state != constants.STATE_SYNC):
        msg = "Load balancer %s state is invalid"
        raise exceptions.ClbException(msg % load_balancer_db.id)
    
    if load_balancer_db.task_state != constants.TASK_NONE:
        msg = "Load balancer %s task state is invalid"
        raise exceptions.ClbException(msg % load_balancer_db.id)


def update_certificate(context, certificate_id, certificate):
    certificate_db = get_resource(context, models.ClbCertificate, 
                                  certificate_id)
    load_balancer_db = get_resource(context, models.LoadBalancer, 
                                    certificate_db.load_balancer_id)

    need_sync = False
    if (('key' in certificate or 'certificate' in certificate) and
        certificate_db.listeners):
        _update_certificate_check(load_balancer_db)
        need_sync = True

    with context.session.begin(subtransactions=True):
        certificate_db.update(certificate)
        if need_sync:
            load_balancer_db.state = constants.STATE_SYNC
    
    return certificate_db.dict()


def delete_certificate(context, certificate_id):
    certificate_db = get_resource(context, models.ClbCertificate, 
                                  certificate_id)

    if certificate_db.listeners:
        msg = "Some listener is using certificate %s"
        raise exceptions.ClbException(msg % certificate_id)
    
    with context.session.begin(subtransactions=True):
        context.session.delete(certificate_db)


def get_certificate(context, certificate_id, fields=None):
    certificate_db = get_resource(context, models.ClbCertificate, 
                                  certificate_id)
    return certificate_db.dict(fields=fields)


def get_certificates(context, filters=None, fields=None):
    return get_resources(context, models.ClbCertificate, filters=filters, 
                         fields=fields)


#################################################
# Listener: Create
#################################################


def _prepare_session_persistence(sp):
    """Prepare session persistence information for listener creating and
    updating."""
    if sp['type'] != constants.SP_APP_COOKIE:
        sp['cookie_name'] = None
    elif not sp.get('cookie_name'):
        msg = ("'cookie_name' must be provided for this type of "
               "session persistence")
        raise exceptions.ClbException(msg)


def _prepare_health_check(hc):
    """Prepare health check information for listener creating and updating."""
    if (hc['type'] == constants.HEALTH_CHECK_HTTP or
        hc['type'] == constants.HEALTH_CHECK_HTTPS):
        hc['http_method'] = hc.get('http_method', 'GET')
        hc['http_url_path'] = hc.get('http_url_path', '/')
        hc['http_expected_codes'] = hc.get('http_expected_codes', '200')
    else:
        hc['http_method'] = None
        hc['http_url_path'] = None
        hc['http_expected_codes'] = None


def _create_session_persistence_db(listener_id, sp):
    # assume all fields provided
    sp_db = models.SessionPersistence(
        listener_id=listener_id,
        type=sp['type'],
        cookie_name=sp['cookie_name']
    )

    return sp_db


def _create_health_check_db(listener_id, hc):
    # assume all fields provided
    hc_db = models.HealthCheck(
        listener_id=listener_id,
        enabled=hc['enabled'],
        type=hc['type'],
        timeout=hc['timeout'],
        delay=hc['delay'],
        fall=hc['fall'],
        rise=hc['rise'],
        http_method=hc['http_method'],
        http_url_path=hc['http_url_path'],
        http_expected_codes=hc['http_expected_codes']
    )

    return hc_db


def _create_listener_check(context, listener, load_balancer_db):
    # NOTE(zcq): The address listen_addr:listen_port should not already
    # be used by other listeners.
    query = context.session.query(models.Listener)
    query = query.filter_by(load_balancer_id=load_balancer_db.id)
    query = query.filter_by(listen_port=listener['listen_port'])
    if query.all():
        msg = "Listener port %(listen_port)d is in use"
        raise exceptions.ClbException(msg % listener)

    if (load_balancer_db.state != constants.STATE_NONE and
        load_balancer_db.state != constants.STATE_SYNC):
        msg = "Load balancer %s state is invalid"
        raise exceptions.ClbException(msg % load_balancer_db.id)
    
    if load_balancer_db.task_state != constants.TASK_NONE:
        msg = "Load balancer %s task state is invalid"
        raise exceptions.ClbException(msg % load_balancer_db.id)


def create_listener(context, listener):
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer, 
                                    listener['load_balancer_id'])
    
    if listener['certificate_id'] is not attributes.ATTR_NOT_SPECIFIED:
        certificate_db = get_resource(context,
                                      models.ClbCertificate,
                                      listener['certificate_id'])
    
    _create_listener_check(context, listener, load_balancer_db)
    
    # Get tenant id from load balancer.
    tenant_id = get_tenant_id_for_create(context, listener)
    listener_id = uuidutils.generate_uuid()

    if listener['certificate_id'] is attributes.ATTR_NOT_SPECIFIED:
        listener['certificate_id'] = None

    with context.session.begin(subtransactions=True):
        listener_db = models.Listener(
            id=listener_id,
            tenant_id=tenant_id,
            state=constants.STATE_NONE,
            task_state=constants.TASK_NONE,
            enabled=listener['enabled'],
            name=listener.get('name'),
            description=listener.get('description'),
            server_protocol=listener['server_protocol'],
            server_maxconn=listener['server_maxconn'],
            listen_addr=listener.get('listen_addr', '0.0.0.0'),
            listen_port=listener['listen_port'],
            load_balance_method=listener['load_balance_method'],
            load_balancer_id=listener['load_balancer_id'],
            certificate_id=listener['certificate_id']
        )
        
        if listener.get('session_persistence'):
            sp = listener['session_persistence']
            _prepare_session_persistence(sp)
            sp_db = _create_session_persistence_db(listener_id, sp)
            listener_db.session_persistence = sp_db

        if listener.get('health_check'):
            hc = listener['health_check']
            _prepare_health_check(hc)
            hc_db = _create_health_check_db(listener_id, hc)
            listener_db.health_check = hc_db

        context.session.add(listener_db)

        load_balancer_db.state = constants.STATE_SYNC
    
    return listener_db.dict()


#################################################
# Listener: Create
#################################################


def _update_session_persistence_db(context, listener_db, sp):
    if listener_db.session_persistence:
        sp_db = listener_db.session_persistence
        if sp == {}:
            with context.session.begin(subtransactions=True):
                context.session.delete(sp_db)
        else:
            with context.session.begin(subtransactions=True):
                _prepare_session_persistence(sp)
                sp_db.update(sp)

    if not listener_db.session_persistence and sp:
        _prepare_session_persistence(sp)
        sp_db = _create_session_persistence_db(listener_db.id, sp)
        listener_db.session_persistence = sp_db


def _update_health_check_db(context, listener_db, hc):
    if listener_db.health_check:
        hc_db = listener_db.health_check
        if hc == {}:
            with context.session.begin(subtransactions=True):
                context.session.delete(hc_db)
        else:
            with context.session.begin(subtransactions=True):
                _prepare_health_check(hc)
                hc_db.update(hc)

    if not listener_db.health_check and hc:
        _prepare_health_check(hc)
        hc_db = _create_health_check_db(listener_db.id, hc)
        listener_db.health_check = hc_db


def update_listener(context, listener_id, listener):
    listener_db = get_resource(context, models.Listener, listener_id)
    lb_id = listener_db.load_balancer_id
    lb_db = get_resource(context, models.LoadBalancer, lb_id)

    if 'listen_port' in listener:
        query = context.session.query(models.Listener)
        query = query.filter(models.Listener.id != listener_id)
        query = query.filter_by(load_balancer_id=lb_id)
        query = query.filter_by(listen_port=listener['listen_port'])
        if query.all():
            msg = "Listener port %(listen_port)d is in use" % listener
            raise exceptions.ClbException(msg)

    if (lb_db.state != constants.STATE_NONE
        and lb_db.state != constants.STATE_SYNC):
        msg = "Load balancer %s state is invalid" % lb_id
        raise exceptions.ClbException(msg)

    if lb_db.task_state != constants.TASK_NONE:
        msg = "Load balancer %s task state is invalid" % lb_id
        raise exceptions.ClbException(msg)

    with context.session.begin(subtransactions=True):
        # has to pop session persistence and health check first
        if 'session_persistence' in listener:
            sp = listener.pop('session_persistence')
            _update_session_persistence_db(context, listener_db, sp)

        if 'health_check' in listener:
            hc = listener.pop('health_check')
            _update_health_check_db(context, listener_db, hc)

        listener_db.update(listener)

        lb_db.state = constants.STATE_SYNC

    return listener_db.dict()


#################################################
# Listener: Delete
#################################################


def _delete_listener_check_load_balancer(load_balancer_db):
    if (load_balancer_db.state != constants.STATE_NONE and
        load_balancer_db.state != constants.STATE_SYNC):
        msg = "Load balancer %s state is invalid"
        raise exceptions.ClbException(msg % load_balancer_db.id)
    
    if load_balancer_db.task_state != constants.TASK_NONE:
        msg = "Load balancer %s task state is invalid"
        raise exceptions.ClbException(msg % load_balancer_db.id)


def delete_listener(context, listener_id):
    listener_db = get_resource(context, models.Listener, listener_id)
    load_balancer_db = get_resource(context, 
                                    models.LoadBalancer,
                                    listener_db.load_balancer_id)
    
    _delete_listener_check_load_balancer(load_balancer_db)

    with context.session.begin(subtransactions=True):
        for backend_db in listener_db.backends:
            context.session.delete(backend_db)
        context.session.delete(listener_db)
        load_balancer_db.state = constants.STATE_SYNC


#################################################
# Listener: Retrieve
#################################################


def get_listener(context, listener_id, fields=None):
    listener_db = get_resource(context, models.Listener, listener_id)
    return listener_db.dict(fields=fields)


def get_listeners(context, filters=None, fields=None):
    return get_resources(context, 
                         models.Listener, 
                         filters=filters, fields=fields)


#################################################
# Backend: Create
#################################################

def _validate_lb_task_none(lb_db):
    if lb_db.task_state != constants.TASK_NONE:
        msg = "Load balancer %s task state is not NONE"
        raise exceptions.ClbException(msg % lb_db.id)


def _validate_lb_state_none_or_sync(lb_db):
    if (lb_db.state != constants.STATE_NONE and
        lb_db.state != constants.STATE_SYNC):
        msg = "Load balancer %s state is not NONE or SYNC"
        raise exceptions.ClbException(msg % lb_db.id)


def _get_load_balancer_db(context, lb_id):
    return get_resource(context, models.LoadBalancer, lb_id)


def _get_backend_db(context, backend_id):
    return get_resource(context, models.Backend, backend_id)


def _get_listener_db(context, listener_id):
    return get_resource(context, models.Listener, listener_id)


def _check_load_balancer_for_backend_operations(lb_db):
    _validate_lb_state_none_or_sync(lb_db)
    _validate_lb_task_none(lb_db)


def _check_backend(context, backend, listener_id):
    query = context.session.query(models.Backend)
    query = query.filter_by(listener_id=listener_id)
    query = query.filter_by(listen_addr=backend['listen_addr'])
    query = query.filter_by(listen_port=backend['listen_port'])
    if query.all():
        msg = "%(listen_addr)s:%(listen_port)d is in use."
        raise exceptions.ClbException(msg % backend)


def create_backend(context, backend):
    listener_db = _get_listener_db(context, backend['listener_id'])
    lb_db = _get_load_balancer_db(context, listener_db.load_balancer_id)

    _validate_lb_state_none_or_sync(lb_db)
    _validate_lb_task_none(lb_db)

    _check_backend(context, backend, backend['listener_id'])

    tenant_id = get_tenant_id_for_create(context, backend)
    
    with context.session.begin(subtransactions=True):
        backend_db = models.Backend(
            id=uuidutils.generate_uuid(),
            tenant_id=tenant_id,
            enabled=backend['enabled'],
            name=backend.get('name'),
            description=backend.get('description'),
            weight=backend['weight'],
            listen_addr=backend['listen_addr'],
            listen_port=backend['listen_port'],
            health_state=constants.HEALTH_UNKNOWN,
            listener_id=backend['listener_id'],
            updated_at=timeutils.strtime()
        )
        context.session.add(backend_db)
        lb_db.state = constants.STATE_SYNC

    return backend_db.dict()


#################################################
# Backend: Update
#################################################


def update_backend(context, backend_id, backend):
    backend_db = _get_backend_db(context, backend_id)
    listener_db = _get_listener_db(context, backend_db.listener_id)
    lb_db = _get_load_balancer_db(context, listener_db.load_balancer_id)

    _validate_lb_state_none_or_sync(lb_db)
    _validate_lb_task_none(lb_db)

    # make sure listen_addr:listen_port pair is not in use.
    listen_addr = backend.get('listen_addr')
    listen_port = backend.get('listen_port')

    if listen_addr is not None or listen_port is not None:
        if listen_addr is None:
            listen_addr = backend_db.listen_addr
        if listen_port is None:
            listen_port = backend_db.listen_port

        query = context.session.query(models.Backend)
        query = query.filter(models.Backend.id != backend_id)
        query = query.filter_by(listener_id=backend_db.listener_id)
        query = query.filter_by(listen_addr=listen_addr)
        query = query.filter_by(listen_port=listen_port)
        if query.all():
            msg = "Update backend %s failed: %s:%d is in use."
            raise exceptions.ClbException(msg % (backend_id, listen_addr,
                                                 listen_port))

    with context.session.begin(subtransactions=True):
        backend_db.update(backend)
        lb_db.state = constants.STATE_SYNC

    return backend_db.dict()


#################################################
# Backend: Delete
#################################################


def delete_backend(context, backend_id):
    backend_db = get_resource(context, models.Backend, backend_id)
    listener_db = get_resource(context, models.Listener, 
                               backend_db.listener_id)
    load_balancer_db = get_resource(context, 
                                models.LoadBalancer,
                                listener_db.load_balancer_id)
    
    _check_load_balancer_for_backend_operations(load_balancer_db)
    
    with context.session.begin(subtransactions=True):
        context.session.delete(backend_db)
        load_balancer_db.state = constants.STATE_SYNC


#################################################
# Backend: Retrieve
#################################################


def get_backend(context, backend_id, fields=None):
    backend_db = get_resource(context, models.Backend, backend_id)
    return backend_db.dict(fields=fields)


def get_backends(context, filters=None, fields=None):
    return get_resources(context, models.Backend, 
                        filters=filters, fields=fields)


def update_backend_health_state(context, backend_id, health_state, updated_at):
    backend_db = get_resource(context, models.Backend, backend_id)
    with context.session.begin(subtransactions=True):
        backend_db.health_state = health_state
        backend_db.updated_at = updated_at

