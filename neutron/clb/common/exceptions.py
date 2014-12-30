from neutron.common import exceptions

class ClbException(exceptions.NeutronException):
    def __init__(self, msg):
        self.message = msg
        super(ClbException, self).__init__()

class NotFound(exceptions.NotFound):
    def __init__(self, msg):
        self.message = msg
        super(NotFound, self).__init__()

###############################################
# resource not found exceptions
###############################################

class LoadBalancerNotFound(NotFound):
    def __init__(self, load_balancer_id):
        msg = "Load balancer %s could not be found" % load_balancer_id
        super(LoadBalancerNotFound, self).__init__(msg)

class InterfaceNotFound(NotFound):
    def __init__(self, interface_id):
        msg = "Interface %s could not be found" % interface_id
        super(InterfaceNotFound, self).__init__(msg)

class BackendNotFound(NotFound):
    def __init__(self, backend_id):
        msg = "Backend %s could not be found" % backend_id
        super(BackendNotFound, self).__init__(msg)

class ListenerNotFound(NotFound):
    def __init__(self, listener_id):
        msg = "Listener %s could not be found" % listener_id
        super(ListenerNotFound, self).__init__(msg)


###########################################
# agent exceptions
###########################################

class NoEligibleAgent(ClbException):
    def __init__(self, load_balancer_id):
        msg = ("No eligible load balancer agent found for "
                "load balancer %s." % load_balancer_id)
        super(NoEligibleAgent, self).__init__(msg)

class NoActiveAgent(ClbException):
    def __init__(self, load_balancer_id):
        msg = ("No active load balancer agent found "
               "for load balancer %s." % load_balancer_id)
        super(NoActiveAgent, self).__init__(msg)

class AgentDriverNotFound(ClbException):
    def __init__(self, provider):
        msg = "Device driver for %s could not be found" % provider
        super(AgentDriverNotFound, self).__init__(msg)

###########################################
# authorization exceptions
###########################################

class NotAuthorized(ClbException):
    def __init__(self):
        msg = "Not authorized."
        super(NotAuthorized, self).__init__(msg)

class AdminRequired(ClbException):
    def __init__(self, msg):
        msg = "User does not have admin privileges: %s" % msg
        super(AdminRequired, self).__init__(msg)


###########################################
# state and task state exceptions
###########################################

class ResourceInOperation(ClbException):
    def __init__(self, model, resource_id):
        msg = "%s %s is in operation" % (model.__name__, resource_id)
        super(ResourceInOperation, self).__init__(msg)

class InvalidState(ClbException):
    def __init__(self, msg):
        super(InvalidState, self).__init__(msg)

class InvalidTaskStateString(ClbException):
    def __init__(self, task_state):
        msg = "%s is not a valid task state" % task_state
        super(InvalidTaskStateString, self).__init__(msg)

class InvalidStateString(ClbException):
    def __init__(self, state):
        msg = "%s is not a valid state" % state
        super(InvalidStateString, self).__init__(msg)

