import abc
from neutron.services import service_base
from neutron.clb.common import constants


class ClbPluginApiBase(service_base.ServicePluginBase):
    __metaclass__ = abc.ABCMeta
    
    def get_plugin_name(self):
        return constants.CLB_PLUGIN_NAME
    
    def get_plugin_type(self):
        return constants.CLB_PLUGIN_NAME
    
    def get_plugin_description(self):
        return "Chinac Load Balance service plugin"

    #########################################
    # load balancer
    #########################################

    @abc.abstractmethod
    def create_load_balancer(self, context, load_balancer):
        pass
    
    @abc.abstractmethod
    def update_load_balancer(self, context, load_balancer_id, load_balancer):
        pass

    @abc.abstractmethod
    def delete_load_balancer(self, context, load_balancer_id):
        pass
    
    @abc.abstractmethod
    def get_load_balancer(self, context, load_balancer_id, fields=None):
        pass

    @abc.abstractmethod
    def get_load_balancers(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def sync_load_balancer(self, context, load_balancer_id):
        pass

    @abc.abstractmethod
    def refresh_routes(self, context, load_balancer_id):
        pass

    ########################################
    # interface
    ########################################
    
    @abc.abstractmethod
    def create_interface(self, context, interface):
        pass
    
    @abc.abstractmethod
    def update_interface(self, context, interface_id, interface):
        pass
    
    @abc.abstractmethod
    def delete_interface(self, context, interface_id):
        pass
    
    @abc.abstractmethod
    def get_interface(self, context, interface_id, fields=None):
        pass
    
    @abc.abstractmethod
    def get_interfaces(self, context, filters=None, fields=None):
        pass

    #########################################
    # certificate operations
    #########################################
    
    @abc.abstractmethod
    def create_certificate(self, context, certificate):
        pass
    
    @abc.abstractmethod
    def update_certificate(self, context, certificate_id, certificate):
        pass
    
    @abc.abstractmethod
    def delete_certificate(self, context, certificate_id):
        pass
    
    @abc.abstractmethod
    def get_certificate(self, context, certificate_id, fields=None):
        pass
    
    @abc.abstractmethod
    def get_certificates(self, context, filters=None, fields=None):
        pass

    ###########################################
    # listener operations
    ###########################################
    
    @abc.abstractmethod
    def create_listener(self, context, listener):
        pass
    
    @abc.abstractmethod
    def update_listener(self, context, listener_id, listener):
        pass
    
    @abc.abstractmethod
    def delete_listener(self, context, listener_id):
        pass
    
    @abc.abstractmethod
    def get_listener(self, context, listener_id, fields=None):
        pass
    
    @abc.abstractmethod
    def get_listeners(self, context, filters=None, fields=None):
        pass
    
    ###########################################
    # backend operations
    ###########################################
    
    @abc.abstractmethod
    def create_backend(self, context, backend):
        pass
    
    @abc.abstractmethod
    def update_backend(self, context, backend_id, backend):
        pass
    
    @abc.abstractmethod
    def delete_backend(self, context, backend_id):
        pass
    
    @abc.abstractmethod
    def get_backend(self, context, backend_id, fields=None):
        pass
    
    @abc.abstractmethod
    def get_backends(self, context, filters=None, fields=None):
        pass

