# -*- coding: utf-8 -*-
'''Exceptions used by :mod:`glorpen.di`.

.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>

'''

class ContainerException(Exception):
    """Base exception"""
    pass

class InjectionException(ContainerException):
    """Raised when service or its method cannot be created or called"""
    def __init__(self, svc_name, cls, method_name=None):
        args = [svc_name, cls.__module__, cls.__name__]
        if method_name is None:
            msg = "Creating service %s (cls: %s.%s) failed"
        else:
            msg = "Calling service %s (cls: %s.%s) method %s(...) failed"
            args.append(method_name)
        
        super(InjectionException, self).__init__(msg % tuple(args))

class UnknownScopeException(ContainerException):
    """Raised when service has *scope* not assigned to :class:`glorpen.di.container.Container` by :meth:`glorpen.di.container.Container.set_scope_hierarchy`."""
    def __init__(self, scope, svc_name):
        super(UnknownScopeException, self).__init__("Unknown scope %r for service %r" % (scope, svc_name))

class UnknownServiceException(ContainerException):
    """Raised when requesting service name which is not registered in :class:`glorpen.di.container.Container`."""
    def __init__(self, svc_name):
        super(UnknownServiceException, self).__init__("Unknown service %r" % (svc_name,))

class UnknownParameterException(ContainerException):
    """Raised when requesting parameter which is not registered in :class:`glorpen.di.container.Container`."""
    def __init__(self, name):
        super(UnknownParameterException, self).__init__("Unknown parameter %r" % (name,))

class ScopeWideningException(ContainerException):
    """Raised when *Service A* depends on *Service B* from narrower scope."""
    def __init__(self, s_def, requester_chain):
        last_def = requester_chain[-1]
        super(ScopeWideningException, self).__init__(
             "Service %s[%s] is requesting %s[%s]. Chain: %s"
             % (last_def.name, last_def._scope.__name__, s_def.name, s_def._scope.__name__,
                " => ".join([i.name for i in requester_chain])
                )
         )
class ServiceAlreadyCreated(ContainerException):
    """Raised when service definition is changed but service is already created by :class:`glorpen.di.container.Container`."""
    def __init__(self, svc_name):
        super(ServiceAlreadyCreated, self).__init__("Service %r is already created and could be in active use" % (svc_name,))

class RecursionException(ContainerException):
    """Raised when service definition is requiring itself."""
    def __init__(self, s_def, requester_chain):
        super(RecursionException, self).__init__(
             "Dependency recursion error, chain was: %s"
             % (" => ".join([i.name for i in requester_chain] + [s_def.name]))
        )

class InvalidAliasTargetException(ContainerException):
    """Raised when adding alias to alias or not exisiting service"""
    def __init__(self, name):
        super(InvalidAliasTargetException, self).__init__(
            "Service %r does not exists or is an alias"
            % name
        )
