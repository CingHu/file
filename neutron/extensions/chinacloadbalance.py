from oslo.config.cfg import CONF

from neutron import manager
from neutron.openstack.common import log
from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import attributes as neutron_attrs

from neutron.clb.common import constants
from neutron.clb.plugin import apibase
from neutron.clb.plugin import attributes as clb_attrs


LOG = log.getLogger(__name__)


class Chinacloadbalance(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return 'Chinac Load Balancing service'
    
    @classmethod
    def get_alias(cls):
        return 'clb'
    
    @classmethod
    def get_description(cls):
        return 'Extension for Chinac Load Balancing service'

    @classmethod
    def get_namespace(cls):
        return 'http://www.chinac.com/doc/clb/api/1.0'
    
    @classmethod
    def get_updated(cls):
        return '2014-05-09T10:00:00-00:00'
    
    @classmethod
    def get_plugin_interface(cls):
        return apibase.ClbPluginApiBase
  
    @classmethod
    def get_resources(cls):
        resources = []
        
        neutron_attrs.PLURALS.update(clb_attrs.PLURALS)
        
        service_plugins = manager.NeutronManager.get_service_plugins()
        plugin = service_plugins[constants.CLB_PLUGIN_NAME] 

        for collection, params in clb_attrs.RESOURCE_ATTRIBUTE_MAP.iteritems():
            member = clb_attrs.PLURALS[collection]
            member_actions = clb_attrs.ACTIONS.get(member, {})

            controller = base.create_resource(
                collection, 
                member,
                plugin,
                params,
                member_actions=member_actions,
                allow_pagination=CONF.allow_pagination,
                allow_sorting=CONF.allow_sorting
            )
            
            resource = extensions.ResourceExtension(
                collection,
                controller,
                path_prefix=constants.CLB_PLUGIN_PREFIX,
                member_actions=member_actions,
                attr_map=params
            )
            
            resources.append(resource)

        return resources
    
    def update_attributes_map(self, attrs):
        super(Chinacloadbalance, self).update_attributes_map(
            attrs,
            extension_attrs_map=clb_attrs.RESOURCE_ATTRIBUTE_MAP
        )
    
    def get_extended_resources(self, version):
        return clb_attrs.RESOURCE_ATTRIBUTE_MAP
