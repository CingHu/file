CLB_AGENT_TYPE = 'Chinac Load Balance Agent'
CLB_PLUGIN_NAME = 'CHINACLOADBALANCE'
CLB_PLUGIN_PREFIX = 'clb'


#
# Object states
#
STATE_INVALID = 'INVALID'
STATE_NONE    = 'NONE'
STATE_ERROR   = 'ERROR'
STATE_SYNC    = 'NEED-SYNC'
STATE_UPDATE  = 'NEED-UPDATE'

INTERFACE_STATES = [STATE_INVALID, 
                    STATE_NONE, 
                    STATE_ERROR, 
                    STATE_UPDATE]

LOAD_BALANCER_STATES = [STATE_INVALID, 
                        STATE_NONE, 
                        STATE_ERROR, 
                        STATE_SYNC]

#
# Object task states
#
TASK_CREATING     = 'CREATING'
TASK_DELETING     = 'DELETING'
TASK_UPDATING     = 'UPDATING'
TASK_NONE         = 'NONE'
TASK_SYNCRONIZING = 'SYNCRONIZING'

INTERFACE_TASK_STATES = [TASK_CREATING, 
                         TASK_DELETING, 
                         TASK_UPDATING,
                         TASK_NONE]

LOAD_BALANCER_TASK_STATES = [TASK_CREATING, 
                             TASK_DELETING, 
                             TASK_SYNCRONIZING, 
                             TASK_NONE]

#
# Device providers for load balance
#
PROVIDER_HAPROXY = 'Haproxy'
PROVIDERS = [PROVIDER_HAPROXY]

# Listener service protocols
PROTOCOL_TCP   = 'TCP'
PROTOCOL_HTTP  = 'HTTP'
PROTOCOL_HTTPS = 'HTTPS'

SERVER_PROTOCOLS = [PROTOCOL_TCP, 
                    PROTOCOL_HTTP, 
                    PROTOCOL_HTTPS]

# Listener load balance methods
LB_METHOD_ROUND_ROBIN       = 'ROUND_ROBIN'
LB_METHOD_LEAST_CONNECTIONS = 'LEAST_CONNECTIONS'
LB_METHOD_SOURCE_IP         = 'SOURCE_IP'

LOAD_BALANCE_METHODS = [LB_METHOD_ROUND_ROBIN, 
                        LB_METHOD_SOURCE_IP,
                        LB_METHOD_LEAST_CONNECTIONS]

# Listener health check types
HEALTH_CHECK_PING  = 'PING'
HEALTH_CHECK_TCP   = 'TCP'
HEALTH_CHECK_HTTP  = 'HTTP'
HEALTH_CHECK_HTTPS = 'HTTPS'

HEALTH_CHECK_TYPES = [HEALTH_CHECK_PING, 
                      HEALTH_CHECK_TCP,
                      HEALTH_CHECK_HTTP, 
                      HEALTH_CHECK_HTTPS]

# Session Persistence types
SP_SOURCE_IP   = 'SOURCE_IP'
SP_HTTP_COOKIE = 'HTTP_COOKIE'
SP_APP_COOKIE  = 'APP_COOKIE'

SESSION_PERSISTENCE_TYPES = [SP_SOURCE_IP, 
                             SP_HTTP_COOKIE, 
                             SP_APP_COOKIE]

# Haproxy server statistics
STATS_ACTIVE_CONNECTIONS = 'active_connections'
STATS_MAX_CONNECTIONS    = 'max_connections'
STATS_TOTAL_CONNECTIONS  = 'total_connections'
STATS_CURRENT_SESSIONS   = 'current_sessions'
STATS_MAX_SESSIONS       = 'max_sessions'
STATS_TOTAL_SESSIONS     = 'total_sessions'
STATS_IN_BYTES           = 'bytes_in'
STATS_OUT_BYTES          = 'bytes_out'
STATS_CONNECTION_ERRORS  = 'connection_errors'
STATS_RESPONSE_ERRORS    = 'response_errors'
STATS_STATUS             = 'status'
STATS_HEALTH             = 'health'
STATS_FAILED_CHECKS      = 'failed_checks'

# Backend health states
HEALTH_ACTIVE  = 'ACTIVE'
HEALTH_DOWN    = 'DOWN'
HEALTH_UNKNOWN = 'UNKNOWN'

# Haproxy Driver namespace prefix
NS_PREFIX = 'clb-'