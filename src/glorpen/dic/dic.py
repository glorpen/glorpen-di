'''
Created on 10 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import inspect
import functools
import importlib

"""
Why not XML:
    XML is bad(tm)

Why not annotations:
    So that object mangled by DI are unaffected, no need to import DI in those modules.
    It should function as helper for developer not as required component as far as used
    classes are concerned.
    ...and creates more problems to solve :)

"""

from glorpen.dic.exceptions import UnknownScopeException, UnknownServiceException, ScopeWideningException, ServiceAlreadyCreated,\
    ContainerException
from glorpen.dic.scopes import ScopePrototype, ScopeSingleton, ScopeBase

def fluid(f):
    functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._frozen:
            raise ServiceAlreadyCreated(self.name)
        else:
            f(self, *args, **kwargs)
        return self
    return wrapper

def normalize_name(o):
    if inspect.isclass(o) or inspect.isfunction(o):
        return "%s.%s" % (o.__module__, o.__qualname__)
    
    if isinstance(o, str):
        return o
    
    raise Exception("Unknown object: %r" % o)

class Deffered(object):
    def __init__(self, service=None, method=None, param=None):
        super(Deffered, self).__init__()
        self.service = service
        self.method = method
        self.param = param
    
    def resolve(self, getter, param_getter):
        if self.service:
            svc = getter(self.service)
            if self.method:
                return getattr(svc, self.method)
            else:
                return svc
        if self.param:
            return param_getter(self.param)
        
        raise Exception()

class Service(object):
    
    SCOPE_SINGLETON = 'singleton'
    SCOPE_PROTOTYPE = 'prototype'
    
    _impl = None
    _impl_getter = None
    
    _factory = None
    _scope = ScopeSingleton
    _load_signature = False
    
    _frozen = False
    
    def __init__(self, name_or_impl, impl=None):
        super(Service, self).__init__()
        
        self._kwargs = {}
        self._sets = {}
        self._calls = []
        self._configurators = []
        self._args_configurators = []
        
        self.name = normalize_name(name_or_impl)
        
        if impl:
            self._impl = impl
        else:
            if callable(name_or_impl):
                self._impl = name_or_impl
            else:
                self._impl_getter = self._lazy_import(name_or_impl)
    
    def _get_implementation(self):
        if self._impl:
            return self._impl
        if self._impl_getter:
            self._impl = self._impl_getter()
            return self._impl
        
        raise ContainerException("Bad implementation argument for %r service" % self.name)
    
    def _lazy_import(self, path):
        module, cls = path.rsplit(".", 1)
        @functools.wraps(self._lazy_import)
        def wrapper(*args, **kwargs):
            return getattr(importlib.import_module(module), cls)
        return wrapper
    
    def _deffer(self, ret=None, svc=None, method=None, param=None):
        if not ret is None:
            return ret
        elif svc or param:
            return Deffered(service=svc, method=method, param=param)
    
    @fluid
    def factory(self, service=None, method=None, callable=None):
        self._factory = self._deffer(svc=service, method=method, ret=callable)
    
    def _normalize_kwargs(self, kwargs):
        kw = {}
        for k,v in kwargs.items():
            if k.endswith("__svc"):
                kw[k[:-5]] = self._deffer(svc=v)
            elif k.endswith("__param"):
                kw[k[:-7]] = self._deffer(param=v)
            else:
                kw[k]=v
        return kw
    
    @fluid
    def kwargs(self, **kwargs):
        self._kwargs.update(self._normalize_kwargs(kwargs))
    
    @fluid
    def call(self, method, **kwargs):
        self._calls.append((False, method, self._normalize_kwargs(kwargs)))
    
    @fluid
    def call_with_signature(self, method, **kwargs):
        self._calls.append((True, method, self._normalize_kwargs(kwargs)))
    
    @fluid
    def set(self, **kwargs):
        self._sets.update(self._normalize_kwargs(kwargs))

    @fluid
    def configurator(self, service=None, method=None, args_method=None, callable=None, args_callable=None):
        if method or callable:
            self._configurators.append(self._deffer(svc=service, method=method, ret=callable))
        if args_method or args_callable:
            self._args_configurators.append(self._deffer(svc=service, method=args_method, ret=args_callable))

    @fluid
    def kwargs_from_signature(self):
        """adds arguments found in class signature, based on provided function hints"""
        self._load_signature = True

    @fluid
    def scope(self, scope_cls):
        self._scope = scope_cls
    
class Container(object):
    
    scopes_cls = []
    scopes = []
    
    def __init__(self):
        super(Container, self).__init__()
        self.services = {}
        self.parameters = {}
        
        self.self_service_name = normalize_name(self.__class__)
        
        self.set_scope_hierarchy(ScopeSingleton, ScopePrototype)
        
    def set_scope_hierarchy(self, *scopes):
        """eg. ScopeSingleton, MyScopeApplication, MyScopeRequest, ScopePrototype"""  
        my_scopes = []
        my_scopes_cls = []
        for scope in scopes:
            if isinstance(scope, ScopeBase):
                my_scopes.append(scope)
                my_scopes_cls.append(scope.__class__)
            else:
                my_scopes.append(scope())
                my_scopes_cls.append(scope)
        
        self.scopes = tuple(my_scopes)
        self.scopes_cls = dict([(o,i) for i,o in enumerate(tuple(my_scopes_cls))])
    
    def add_service(self, name):
        s = Service(name)
        self.services[s.name] = s
        return s
    
    def add_parameter(self, name, value):
        self.parameters[name] = value
    
    def get(self, svc):
        return self._get(svc)
    
    def get_parameter(self, name):
        if name in self.parameters:
            return self.parameters[name]
        else:
            raise UnknownServiceException(name)
    
    def get_definition(self, svc):
        name = normalize_name(svc)
        if not name in self.services:
            raise UnknownServiceException(name)
        
        return self.services[name]
    
    def _get(self, svc, requester_chain=None):
        name = normalize_name(svc)
        
        if name == self.self_service_name:
            return self
        
        if not name in self.services:
            raise UnknownServiceException(name)
        
        s_def = self.services.get(name)
        
        my_scope = s_def._scope
        
        if not my_scope in self.scopes_cls:
            raise UnknownScopeException(my_scope, s_def)
        
        
        scope_index = self.scopes_cls[my_scope]
        
        if not requester_chain:
            requester_chain = []
        else:
            requester_scope = requester_chain[-1]._scope
            if requester_scope and scope_index > self.scopes_cls[requester_scope]:
                raise ScopeWideningException(s_def, requester_chain)
        
        def resolver(value):
            if isinstance(value, Deffered):
                return value.resolve(lambda name:self._get(name, requester_chain + [s_def]), self.get_parameter)
            else:
                return value
        
        def service_creator():
            return self._create(s_def, resolver)
        
        return self.scopes[scope_index].get(service_creator, name)
    
    def _update_kwargs_from_signature(self, function, kwargs):
        sig = inspect.signature(function)
        for name, param in tuple(sig.parameters.items()):
            if name == "self":
                continue
            if param.annotation is inspect.Parameter.empty:
                continue
            n = normalize_name(param.annotation)
            if n in self.services:
                kwargs.setdefault(name, Deffered(service=n))
        
    
    def _create(self, s_def, resolver):
        
        s_def._frozen = True
        
        def resolve_kwargs(kwargs):
            return dict([(k, resolver(v)) for k,v in kwargs.items()])
        
        if s_def._factory:
            cls = resolver(s_def._factory)
        else:
            cls = s_def._get_implementation()
        
        kwargs = dict(s_def._kwargs)
        self._update_kwargs_from_signature(cls.__init__, kwargs)
        kwargs = resolve_kwargs(kwargs)
        
        for conf in s_def._args_configurators:
            resolver(conf)(kwargs)
        
        instance = cls(**kwargs)
        
        for conf in s_def._configurators:
            resolver(conf)(instance)
        
        for k,v in resolve_kwargs(s_def._sets).items():
            setattr(instance, k, v)
        
        for use_sig, call_method, call_kwargs in s_def._calls:
            callable = getattr(instance, call_method)
            kwargs = dict(call_kwargs)
            if use_sig:
                self._update_kwargs_from_signature(callable, kwargs)
            callable(**resolve_kwargs(kwargs))
        
        return instance
