from neutron.api.v2 import attributes
from neutron.clb.common import constants


LOAD_BALANCER_ATTR_MAP = {
    'id': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True,
        'primary_key': True,
    },
    'tenant_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:string': None},
        'is_visible': True,
        'required_by_policy': True,
    },
    'name': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
        'default': '',
    },
    'description': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
        'default': '',
    },
    'provider': {
        'allow_post': True,
        'allow_put': False,
        'default': constants.PROVIDER_HAPROXY,
        'validate': {'type:values': constants.PROVIDERS},
        'is_visible': True,
    },
    'maxconn': {
        'allow_post': True,
        'allow_put': True,
        'default': -1,
        'convert_to': attributes.convert_to_int,
        'is_visible': True
    },
    'state': {
        'allow_post': False,
        'allow_put': True,
        'validate': {'type:values': constants.LOAD_BALANCER_STATES},
        'is_visible': True
    },
    'task_state': {
        'allow_post': False,
        'allow_put': True,
        'validate': {'type:values': constants.LOAD_BALANCER_TASK_STATES},
        'is_visible': True
    },
}


CERTIFICATE_ATTR_MAP = {
    'id': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True,
        'primary_key': True
    },
    'tenant_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:string': None},
        'is_visible': True,
    },
    'name': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
        'default': '',
    },
    'description': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
        'default': '',
    },
    'load_balancer_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True
    },
    'certificate': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
    },
    'key': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
    },
}


INTERFACE_ATTR_MAP = {
    'id': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True,
        'primary_key': True
    },
    'tenant_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:string': None},
        'is_visible': True,
    },
    'enabled': {
        'allow_post': False,
        'allow_put': False,
        'convert_to': attributes.convert_to_boolean,
        'default': True,
        'is_visible': True
    },
    'is_public': {
        'allow_post': True,
        'allow_put': False,
        'convert_to': attributes.convert_to_boolean,
        'default': True,
        'is_visible': True
    },
    'state': {
        'allow_post': False,
        'allow_put': True,
        'validate': {'type:values': constants.INTERFACE_STATES},
        'is_visible': True
    },
    'task_state': {
        'allow_post': False,
        'allow_put': True,
        'validate': {'type:values': constants.INTERFACE_TASK_STATES},
        'is_visible': True
    },
    'load_balancer_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True
    },
    'subnet_id': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:uuid': None},
        'is_visible': True
    },
    'mac_address': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:mac_address': None},
        'default': attributes.ATTR_NOT_SPECIFIED,
        'is_visible': True
    }, 
    'ip_address': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:ip_address': None},
        'default': attributes.ATTR_NOT_SPECIFIED,
        'is_visible': True
    },
    'port_id': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True
    },
    'inbound_limit': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:non_negative': None},
        'convert_to': attributes.convert_to_int,
        'default': 0,
        'is_visible': True
    },
    'outbound_limit': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:non_negative': None},
        'convert_to': attributes.convert_to_int,
        'default': 0,
        'is_visible': True
    },
}


LISTENER_ATTR_MAP = {
    'id': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True,
        'primary_key': True
    },
    'tenant_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:string': None},
        'is_visible': True,
    },
    'load_balancer_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True
    },
    'certificate_id': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:uuid': None},
        'default': attributes.ATTR_NOT_SPECIFIED,
        'is_visible': True
    },
    'name': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'default': '',
        'is_visible': True
    },
    'description': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'default': '',
        'is_visible': True
    },
    'enabled': {
        'allow_post': True,
        'allow_put': True,
        'convert_to': attributes.convert_to_boolean,
        'default': True,
        'is_visible': True
    },
    'server_protocol': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:values': constants.SERVER_PROTOCOLS},
        'is_visible': True
    },
    'listen_addr': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:ip_address': None},
        'default': '0.0.0.0',
        'is_visible': True
    },
    'listen_port': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:range': [0, 65535]},
        'convert_to': attributes.convert_to_int,
        'is_visible': True
    },
    'server_maxconn': {
        'allow_post': True,
        'allow_put': True,
        'default': -1,
        'convert_to': attributes.convert_to_int,
        'is_visible': True
    },
    'load_balance_method': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:values': constants.LOAD_BALANCE_METHODS},
        'is_visible': True
    },
    'session_persistence': {
        'allow_post': True,
        'allow_put': True,
        'convert_to': attributes.convert_none_to_empty_dict,
        'default': {},
        'validate': {
            'type:dict_or_empty': {
                'type': {
                    'type:values': constants.SESSION_PERSISTENCE_TYPES,
                    'required': True
                },
                'cookie_name': {
                    'type:string': None,
                    'required': False
                }
            }
        },
        'is_visible': True
    },
    'health_check': {
        'allow_post': True,
        'allow_put': True,
        'convert_to': attributes.convert_none_to_empty_dict,
        'default': {},
        'validate': {
            'type:dict_or_empty': {
                'enabled': {
                    'convert_to': attributes.convert_to_boolean,
                    'required': True,
                    'default': True,
                },
                'type': {
                    'type:values': constants.HEALTH_CHECK_TYPES,
                    'required': True,
                },
                'timeout': {
                    'type:non_negative': None,
                    'convert_to': attributes.convert_to_int,
                    'required': True,
                },
                'delay': {
                    'type:non_negative': None,
                    'convert_to': attributes.convert_to_int,
                    'required': True,
                },
                'fall': {
                    'type:range': [1, 10],
                    'convert_to': attributes.convert_to_int,
                    'required': True,
                },
                'rise': {
                    'type:range': [1, 10],
                    'convert_to': attributes.convert_to_int,
                    'required': True,
                },
                'http_method': {
                    'type:string': None,
                    'required': False,
                },
                'http_url_path': {
                    'type:string': None,
                    'required': False,
                },
                'http_expected_codes': {
                    'type:regex': '^(\d{3}(\s*,\s*\d{3})*)$|^(\d{3}-\d{3})$',
                    'required': False,
                }
            }
        },
        'is_visible': True
    }
}


BACKEND_ATTR_MAP = {
    'id': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True,
        'primary_key': True
    },
    'tenant_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:string': None},
        'is_visible': True,
    },
    'name': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
        'default': '',
    },
    'description': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:string': None},
        'is_visible': True,
        'default': '',
    },
    'enabled': {
        'allow_post': True,
        'allow_put': True,
        'convert_to': attributes.convert_to_boolean,
        'default': True,
        'is_visible': True
    },
    'listen_addr': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:ip_address': None},
        'is_visible': True
    },
    'listen_port': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:range': [0, 65535]},
        'convert_to': attributes.convert_to_int,
        'is_visible': True
    },
    'weight': {
        'allow_post': True,
        'allow_put': True,
        'validate': {'type:range': [0, 256]},
        'convert_to': attributes.convert_to_int,
        'default': 1,        
        'is_visible': True
    },
    'listener_id': {
        'allow_post': True,
        'allow_put': False,
        'validate': {'type:uuid': None},
        'is_visible': True
    },
    'health_state': {
        'allow_post': False,
        'allow_put': False,
        'validate': {'type:string': None},
        'is_visible': True
    }
}


RESOURCE_ATTRIBUTE_MAP = {
    'load_balancers': LOAD_BALANCER_ATTR_MAP,
    'certificates': CERTIFICATE_ATTR_MAP,
    'interfaces': INTERFACE_ATTR_MAP,
    'listeners': LISTENER_ATTR_MAP,
    'backends': BACKEND_ATTR_MAP
}


PLURALS = {
    'load_balancers': 'load_balancer',
    'interfaces': 'interface',
    'listeners': 'listener',
    'backends': 'backend',
    'certificates': 'certificate'
}


LOAD_BALANCER_ACTIONS = {
    'sync_load_balancer': 'POST',
    'refresh_routes': 'POST',
}


ACTIONS = {
    'load_balancer': LOAD_BALANCER_ACTIONS,
}
