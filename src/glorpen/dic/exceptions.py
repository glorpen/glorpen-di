'''
Created on 10 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

class ContainerException(Exception):
    pass

class UnknownScopeException(ContainerException):
    def __init__(self, scope, svc_name):
        super(UnknownScopeException, self).__init__("Unknown scope %r for service %r" % (scope, svc_name))

class UnknownServiceException(ContainerException):
    def __init__(self, svc_name):
        super(UnknownServiceException, self).__init__("Unknown service %r" % (svc_name,))

class ScopeWideningException(ContainerException):
    def __init__(self, s_def, requester_chain):
        last_def = requester_chain[-1]
        super(ScopeWideningException, self).__init__(
             "Service %s[%s] is requesting %s[%s]. Chain: %s"
             % (last_def.name, last_def._scope.__name__, s_def.name, s_def._scope.__name__,
                " => ".join([i.name for i in requester_chain])
                )
         )
class ServiceAlreadyCreated(ContainerException):
    def __init__(self, svc_name):
        super(ServiceAlreadyCreated, self).__init__("Service %r is already created and could be in active use" % (svc_name,))
