# -*- coding: utf-8 -*-
'''

.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>

'''
import inspect
import functools
import importlib
import six

from glorpen.di import exceptions
from glorpen.di.scopes import ScopePrototype, ScopeSingleton, ScopeBase

try:
    from inspect import signature
    signature_empty = inspect.Parameter.empty
except ImportError:
    from funcsigs import signature
    from funcsigs import _empty as signature_empty

def fluid(f):
    """Decorator for applying fluid pattern to class methods
    and to disallow calling when instance is marked as frozen.
    """
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._frozen:
            raise exceptions.ServiceAlreadyCreated(self.name)
        else:
            f(self, *args, **kwargs)
        return self
    return wrapper

def normalize_name(o):
    """Gets object "name" for use with :class:`.Container`.
    
    Args:
        o (object): Object to get name for
    
    Returns:
        str
    
    Raises:
        Exception
    
    """
    if inspect.isclass(o) or inspect.isfunction(o):
        return "%s.%s" % (o.__module__, o.__name__)
    
    if isinstance(o, str):
        return o
    
    raise Exception("Unknown object: %r" % o)

class Deffered(object):
    """Class for marking values for lazy resolving.
    
    Values are resolved by :class:`.Container` upon service creation.
    """
    def __init__(self, service=None, method=None, param=None):
        super(Deffered, self).__init__()
        self.service = service
        self.method = method
        self.param = param
    
    def resolve(self, getter, param_getter):
        """Given (service) getter and param_getter, returns resolved value."""
        if self.service:
            svc = getter(self.service)
            if self.method:
                return getattr(svc, self.method)
            else:
                return svc
        if self.param:
            return param_getter(self.param)
        
        raise Exception()

class Kwargs(object):
    """Simply wraps given kwargs for later use."""
    def __init__(self, **kwargs):
        super(Kwargs, self).__init__()
        self.kwargs = kwargs
    
    @classmethod
    def merge(cls, *args):
        """Merges iterable arguments, can be `dict` or :class:`.Kwargs` instance.
        @return: Resulting dict
        """
        ret = {}
        for arg in args:
            if arg is None:
                continue
            if isinstance(arg, cls):
                arg = arg.kwargs
            ret.update(arg)
        
        return ret

class Service(object):
    """Service definition.
    
    When filling arguments for constructor and method calls you can use:
    
    - `my_var__svc=MyClass` - will inject service MyClass to `my_var`
    - `my_var__param="my.param"` - will inject parameter named "my.param" to `my_var`
    
    Implementation value for service can be:
    
    - class instance
    - string with import path
    - callable
    
    """
    
    _impl = None
    _name_or_impl = None
    
    _factory = None
    _scope = ScopeSingleton
    _load_signature = False
    
    _frozen = False
    
    def __init__(self, name_or_impl):
        super(Service, self).__init__()
        
        self._kwargs = {}
        self._sets = {}
        self._calls = []
        self._configurators = []
        self._kwargs_modifiers = []
        
        self.name = normalize_name(name_or_impl)
        self._name_or_impl = name_or_impl
    
    def _get_implementation(self):
        if self._impl:
            return self._impl
        
        if callable(self._name_or_impl):
            return self._name_or_impl
        else:
            return self._lazy_import(self._name_or_impl)()
        
        raise exceptions.ContainerException("Bad implementation argument for %r service" % self.name)
    
    def _lazy_import(self, path):
        """Wraps import path in callable returning class object"""
        module, cls = path.rsplit(".", 1)
        @functools.wraps(self._lazy_import)
        def wrapper(*args, **kwargs):
            return getattr(importlib.import_module(module), cls)
        return wrapper
    
    def _deffer(self, ret=None, svc=None, method=None, param=None):
        """Wraps value in :class:`.Deffered`. If *ret* argument is given it is returned unchanged."""
        if not ret is None:
            return ret
        elif svc or param:
            return Deffered(service=svc, method=method, param=param)
    
    @fluid
    def implementation(self, v):
        """Sets service implementation (callable).
        
        Returns:
            :class:`.Service`
        """
        self._impl = v
    
    @fluid
    def factory(self, service=None, method=None, callable=None, kwargs=None, **kwargs_inline):
        """Sets factory callable.
        
        Returns:
            :class:`.Service`"""
        self._factory = (self._deffer(svc=service, method=method, ret=callable), self._normalize_kwargs(kwargs_inline, kwargs))
    
    def _normalize_kwargs(self, *args):
        kwargs = Kwargs.merge(*args)
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
        """Adds service constructor arguments.
        
        Returns:
            :class:`.Service`"""
        self._kwargs.update(self._normalize_kwargs(kwargs))
    
    @fluid
    def call(self, method, kwargs=None, **kwargs_inline):
        """Adds a method call after service creation with given arguments.
        
        Returns:
            :class:`.Service`"""
        self._calls.append((False, method, self._normalize_kwargs(kwargs_inline, kwargs)))
    
    @fluid
    def call_with_signature(self, method, kwargs=None, **kwargs_inline):
        """Adds a method call after service creation with given arguments.
        Arguments detected from function signature are added if not already present.
        
        Returns:
            :class:`.Service`"""
        self._calls.append((True, method, self._normalize_kwargs(kwargs_inline, kwargs)))
    
    @fluid
    def set(self, **kwargs):
        """Will :func:`setattr` given arguments on service.
        
        Returns:
            :class:`.Service`"""
        self._sets.update(self._normalize_kwargs(kwargs))

    @fluid
    def configurator(self, service=None, method=None, callable=None, kwargs=None, **kwargs_inline):
        """Adds service or callable as configurator of this service.
        
        Args:
            service + method, callable: given service method/callable will be called with instance of this service.
        
        Returns:
            :class:`.Service`
        """
        if method or callable:
            self._configurators.append((self._deffer(svc=service, method=method, ret=callable), self._normalize_kwargs(kwargs_inline, kwargs)))

    @fluid
    def kwargs_modifier(self, service=None, method=None, callable=None, kwargs=None, **kwargs_inline):
        """Adds service or callable as constructor arguments modifier of this service.
        
        Args:
            service + method, callable: given service method/callable will be called with kwargs of this service.
        
        Returns:
            :class:`.Service`
        """
        if method or callable:
            self._kwargs_modifiers.append((self._deffer(svc=service, method=method, ret=callable), self._normalize_kwargs(kwargs_inline, kwargs)))

    @fluid
    def kwargs_from_signature(self):
        """Adds arguments found in class signature, based on provided function hints.
        
        Returns:
            :class:`.Service`
        """
        self._load_signature = True

    @fluid
    def scope(self, scope_cls):
        """Sets service scope.
        
        Returns:
            :class:`.Service`
        """
        self._scope = scope_cls

class Alias(object):
    """Alias for service."""
    def __init__(self, target):
        super(Alias, self).__init__()
        self.target = normalize_name(target)

class Container(object):
    """Implementation of DIC container."""
    
    scopes_cls = []
    scopes = []
    
    def __init__(self):
        super(Container, self).__init__()
        self.services = {}
        self.parameters = {}
        
        self.self_service_name = normalize_name(self.__class__)
        
        self.set_scope_hierarchy(ScopeSingleton, ScopePrototype)
        
    def set_scope_hierarchy(self, *scopes):
        """Sets used scopes hierarchy.
        
        Arguments should be scopes sorted from widest to narrowest.
        A service in wider scope cannot request service from narrower one.
        
        Default is: [:class:`glorpen.di.scopes.ScopeSingleton`, :class:`glorpen.di.scopes.ScopePrototype`].
        
        Args:
            classes or instances of :class:`glorpen.di.scopes.ScopeBase`
        
        """  
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
        """Adds service definition to this container.
        
        *name* argument should be a class, import path, or string if :meth:`.Service.implementation` will be used.
        
        Returns:
            :class:`.Service`
        
        """
        s = Service(name)
        self.services[s.name] = s
        return s
    
    def add_alias(self, service, alias):
        """Adds an alias for given service"""
        a = Alias(service)
        if not a.target in self.services or not isinstance(self.services[a.target], Service):
            raise exceptions.InvalidAliasTargetException(a.target)
        self.services[alias] = a
        return a
    
    def add_parameter(self, name, value):
        """Adds a key-value parameter."""
        self.parameters[name] = value
    
    def get(self, svc):
        """Gets service instance.
        
        Raises:
            UnkownServiceException
        
        """
        try:
            return self._get(svc)
        except exceptions.ContainerException as e:
            six.reraise(e.__class__, e)
    
    def get_parameter(self, name):
        """Gets parameter.
        
        Raises:
            UnkownParameterException
        
        """
        if name in self.parameters:
            return self.parameters[name]
        else:
            raise exceptions.UnknownParameterException(name)
    
    def get_definition(self, svc):
        """Returns definition for given service name."""
        name = normalize_name(svc)
        if not name in self.services:
            raise exceptions.UnknownServiceException(name)
        
        return self.services[name]
    
    def _get_service_definition(self, name):
        s = self.services.get(name)
        if hasattr(s, "target"):
            return self.services.get(s.target)
        return s
    
    def _get(self, svc, requester_chain=None):
        name = normalize_name(svc)
        
        if name == self.self_service_name:
            return self
        
        if not name in self.services:
            raise exceptions.UnknownServiceException(name)
        
        s_def = self._get_service_definition(name)
        
        my_scope = s_def._scope
        
        if not my_scope in self.scopes_cls:
            raise exceptions.UnknownScopeException(my_scope, s_def)
        
        scope_index = self.scopes_cls[my_scope]
        
        if not requester_chain:
            requester_chain = []
        else:
            requester_scope = requester_chain[-1]._scope
            if requester_scope and scope_index > self.scopes_cls[requester_scope]:
                raise exceptions.ScopeWideningException(s_def, requester_chain)
        
        def resolver(value):
            if isinstance(value, Deffered):
                if s_def in requester_chain:
                    raise exceptions.RecursionException(s_def, requester_chain)
                return value.resolve(lambda name:self._get(name, requester_chain + [s_def]), self.get_parameter)
            else:
                return value
        
        def service_creator():
            return self._create(s_def, resolver)
        
        return self.scopes[scope_index].get(service_creator, name)
    
    def _update_kwargs_from_signature(self, function, kwargs):
        try:
            sig = signature(function)
        except ValueError:
            return
        
        for name, param in tuple(sig.parameters.items()):
            if name == "self":
                continue
            
            if param.annotation is signature_empty:
                continue
            n = normalize_name(param.annotation)
            if n in self.services:
                kwargs.setdefault(name, Deffered(service=n))
        
    
    def _create(self, s_def, resolver):
        
        s_def._frozen = True
        
        def resolve_kwargs(kwargs):
            return dict([(k, resolver(v)) for k,v in kwargs.items()])
        
        if s_def._factory:
            cls = resolver(s_def._factory[0])
            kwargs = s_def._factory[1]
        else:
            cls = s_def._get_implementation()
            kwargs = {}
        
        kwargs.update(s_def._kwargs)
        self._update_kwargs_from_signature(cls.__init__, kwargs)
        kwargs = resolve_kwargs(kwargs)
        
        for conf, params in s_def._kwargs_modifiers:
            resolver(conf)(kwargs, **resolve_kwargs(params))
        
        try:
            instance = cls(**kwargs)
        except Exception as e:
            six.raise_from(exceptions.InjectionException(s_def.name, cls), e)
        
        for conf, params in s_def._configurators:
            resolver(conf)(instance, **resolve_kwargs(params))
        
        for k,v in resolve_kwargs(s_def._sets).items():
            setattr(instance, k, v)
        
        for use_sig, call_method, call_kwargs in s_def._calls:
            callable = getattr(instance, call_method)
            kwargs = dict(call_kwargs)
            if use_sig:
                self._update_kwargs_from_signature(callable, kwargs)
            
            try:
                callable(**resolve_kwargs(kwargs))
            except Exception as e:
                six.raise_from(exceptions.InjectionException(s_def.name, cls, call_method), e)
        
        return instance
