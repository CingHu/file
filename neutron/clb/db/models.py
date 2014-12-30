from sqlalchemy import Column, ForeignKey
from sqlalchemy import String, Boolean, Integer, BigInteger, DateTime
from sqlalchemy.orm import validates
from sqlalchemy.orm import relationship, backref
from neutron.db.model_base import BASEV2
from neutron.db.models_v2 import Port
from neutron.db.agents_db import Agent


class HasId(object):
    id = Column(String(36), primary_key=True)


class HasState(object):
    state = Column(String(32), nullable=False)
    task_state = Column(String(64), nullable=False)


class HasTenant(object):
    tenant_id = Column(String(255), nullable=False)


class HasDesc(object):
    name = Column(String(128))
    description = Column(String(255))


class HasEnabled(object):
    enabled = Column(Boolean(), nullable=False)    


#########################################################
# Load balance database model base
#########################################################

class FieldMixin(object):

    def _fields(self, resource, fields):
        if fields:
            return dict(((key, item)
                         for key, item in resource.items()
                         if key in fields))
        return resource


#########################################################
# Load balance database models
#########################################################

class LoadBalancer(BASEV2, FieldMixin, HasId, HasTenant, HasState, HasDesc):
    __tablename__ = 'clb_load_balancers'

    maxconn  = Column(Integer, nullable=False)
    provider = Column(String(32), nullable=False)

    def dict(self, fields=None):
        load_balancer = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'state': self.state,
            'task_state': self.task_state,
            'provider': self.provider,
            'maxconn': self.maxconn
        }
        
        if self.name is not None:
            load_balancer['name'] = self.name
        if self.description is not None:
            load_balancer['description'] = self.description

        if self.listeners:
            load_balancer['listeners'] = [listener.id 
                                          for listener in self.listeners]
        if self.interfaces:
            load_balancer['interfaces'] = [interface.id
                                           for interface in self.interfaces]
        
        if self.certificates:
            load_balancer['certificates'] = [certificate.id
                                             for certificate in self.certificates]
        
        return self._fields(load_balancer, fields)


class Interface(BASEV2, FieldMixin, HasId, HasTenant, HasState, HasEnabled):
    __tablename__ = 'clb_interfaces'
    
    inbound_limit    = Column(Integer, nullable=False)
    outbound_limit   = Column(Integer, nullable=False)
    port_id          = Column(String(36), 
                              ForeignKey('ports.id'))
    load_balancer_id = Column(String(36),
                              ForeignKey('clb_load_balancers.id'),
                              nullable=False)
    is_public        = Column(Boolean(), nullable=False)

    port =          relationship(Port)
    load_balancer = relationship(LoadBalancer,
                                 backref=backref('interfaces'))

    def dict(self, fields=None):
        interface = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'state': self.state,
            'task_state': self.task_state,
            'enabled': self.enabled,
            'load_balancer_id': self.load_balancer_id,
            'inbound_limit': self.inbound_limit,
            'outbound_limit': self.outbound_limit,
            'is_public': self.is_public
        }
        
        if self.port_id:
            interface['port_id'] = self.port_id
            interface['mac_address'] = self.port.mac_address
            if self.port.fixed_ips:
                fixed_ip = self.port.fixed_ips[0]
                interface['subnet_id'] = fixed_ip['subnet_id']
                interface['ip_address'] = fixed_ip['ip_address']

        return self._fields(interface, fields)


class Listener(BASEV2, FieldMixin, HasId, HasTenant, HasState, HasDesc, HasEnabled):
    __tablename__ = 'clb_listeners'
    
    server_protocol     = Column(String(64), nullable=False)
    server_maxconn      = Column(Integer, nullable=False)
    listen_addr         = Column(String(64), nullable=False)
    listen_port         = Column(Integer, nullable=False)
    load_balance_method = Column(String(64), nullable=False)
    load_balancer_id    = Column(String(36), 
                                 ForeignKey('clb_load_balancers.id'),
                                 nullable=False)
    certificate_id      = Column(String(36),
                                 ForeignKey('clb_certificates.id'))
    
    certificate         = relationship('ClbCertificate',
                                       backref=backref('listeners'))
    load_balancer       = relationship('LoadBalancer',
                                       backref=backref('listeners'))
    session_persistence = relationship('SessionPersistence',
                                       uselist=False,
                                       backref='listener',
                                       cascade='all, delete-orphan')
    health_check        = relationship('HealthCheck',
                                       uselist=False,
                                       backref='listener',
                                       cascade='all, delete-orphan')

    def dict(self, fields=None):
        listener = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'state': self.state,
            'task_state': self.task_state,
            'enabled': self.enabled,
            'server_protocol': self.server_protocol,
            'server_maxconn': self.server_maxconn,
            'listen_addr': self.listen_addr,
            'listen_port': self.listen_port,
            'load_balance_method': self.load_balance_method,
            'load_balancer_id': self.load_balancer_id
            
        }

        if self.certificate_id:
            listener['certificate_id'] = self.certificate_id

        if self.name is not None:
            listener['name'] = self.name

        if self.description is not None:
            listener['description'] = self.description

        if self.session_persistence:
            listener['session_persistence'] = self.session_persistence.dict()

        if self.health_check:
            listener['health_check'] = self.health_check.dict()
        
        if self.backends:
            listener['backends'] = [backend.id 
                                    for backend in self.backends]
        
        return self._fields(listener, fields)


class SessionPersistence(BASEV2, FieldMixin):
    __tablename__ = 'clb_session_persistences'
    
    listener_id = Column(String(36),
                         ForeignKey("clb_listeners.id"),
                         primary_key=True)
    type        = Column(String(64), nullable=False)
    cookie_name = Column(String(1024))

    def dict(self, fields=None):
        session_persistence = {
            'type': self.type
        }
        
        if self.cookie_name:
            session_persistence['cookie_name'] = self.cookie_name
        
        return self._fields(session_persistence, fields)


class HealthCheck(BASEV2, FieldMixin, HasEnabled):
    __tablename__ = 'clb_health_checks'
    
    listener_id         = Column(String(36),
                                 ForeignKey("clb_listeners.id"),
                                 primary_key=True)
    type                = Column(String(32), nullable=False)
    timeout             = Column(Integer, nullable=False)
    delay               = Column(Integer, nullable=False)
    fall                = Column(Integer, nullable=False)
    rise                = Column(Integer, nullable=False)
    http_method         = Column(String(16))
    http_url_path       = Column(String(255))
    http_expected_codes = Column(String(255))

    def dict(self, fields=None):
        health_check = {
            'type': self.type,
            'enabled': self.enabled,
            'timeout': self.timeout,
            'delay': self.delay,
            'rise': self.rise,
            'fall': self.fall,
            'http_method': self.http_method,
            'http_url_path': self.http_url_path,
            'http_expected_codes': self.http_expected_codes
        }
        
        return self._fields(health_check, fields)


class LoadBalancerAgentBinding(BASEV2, FieldMixin):
    __tablename__ = 'clb_load_balancer_agent_bindings'
    
    load_balancer_id = Column(String(36),
                              ForeignKey('clb_load_balancers.id',
                                         ondelete='CASCADE'),
                              primary_key=True)
    agent_id         = Column(String(36),
                              ForeignKey('agents.id', 
                                         ondelete='CASCADE'))
    agent = relationship(Agent)
    

class Backend(BASEV2, FieldMixin, HasId, HasTenant, HasDesc, HasEnabled):
    __tablename__ = 'clb_backends'
    
    listener_id  = Column(String(36),
                          ForeignKey('clb_listeners.id'), 
                          nullable=False)
    weight       = Column(Integer, nullable=False)
    listen_addr  = Column(String(64), nullable=False)
    listen_port  = Column(Integer, nullable=False)
    health_state = Column(String(36), nullable=False)
    updated_at   = Column(DateTime, nullable=False)

    listener     = relationship('Listener',
                                backref=backref('backends'))

    def dict(self, fields=None):
        backend = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'enabled': self.enabled,
            'listener_id': self.listener_id,
            'weight': self.weight,
            'listen_addr': self.listen_addr,
            'listen_port': self.listen_port,
            'health_state': self.health_state
        }
        
        if self.name is not None:
            backend['name'] = self.name
        if self.description is not None:
            backend['description'] = self.description
        
        return self._fields(backend, fields)


class ClbCertificate(BASEV2, FieldMixin, HasId, HasTenant, HasDesc):
    __tablename__ = 'clb_certificates'
    
    load_balancer_id    = Column(String(36), 
                                 ForeignKey('clb_load_balancers.id'),
                                 nullable=False)
    certificate         = Column(String(2048), nullable=False)
    key                 = Column(String(2048), nullable=False)
    load_balancer       = relationship('LoadBalancer',
                                       backref=backref('certificates'))

    def dict(self, fields=None):
        certificate = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'load_balancer_id': self.load_balancer_id,
            'certificate': self.certificate,
            'key': self.key
        }

        if self.name is not None:
            certificate['name'] = self.name
        if self.description is not None:
            certificate['description'] = self.description

        return self._fields(certificate, fields)


class ListenerStatistics(BASEV2, FieldMixin):
    __tablename__ = 'clb_listener_statistics'
    
    listener_id         = Column(String(36),
                                 ForeignKey('clb_listeners.id'),
                                 primary_key=True)
    listener = relationship('Listener',
                            backref=backref('statistics'))
    bytes_in            = Column(BigInteger, nullable=False)
    bytes_out           = Column(BigInteger, nullable=False)
    active_connections  = Column(BigInteger, nullable=False)
    total_connections   = Column(BigInteger, nullable=False)
    
    @validates('bytes_in', 'bytes_out',
               'active_connections', 'total_connections')
    def validate_non_negative_int(self, key, value):
        if value < 0:
            data = {'key': key, 'value': value}
            raise ValueError('The %(key)s field can not have '
                             'negative value. '
                             'Current value is %(value)d.' % data)
        return value
    
    def dict(self, fields=None):
        statistics = {
            'bytes_in': self.bytes_in,
            'bytes_out': self.bytes_out,
            'active_connections': self.active_connections,
            'total_connections': self.total_connections
        }
        
        return self._fields(statistics, fields)


