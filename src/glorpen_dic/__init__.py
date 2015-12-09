'''
Created on 9 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import inspect
import logging
import functools

class Container(object):
    """Dependency injection the Python way. Or so I think.
    
    Usage
    -----
    
    As instance:
    
        c = Container()
        
        c.parameter("di-value", "some value")
        
        @c.provider
        class MyClass(object)
            @c.params(value="di-value")
            def method(value)
                print(value)
        
        c.get(MyClass).method()
        
    If you don't want to have global DI instance you can use it as registry:
        
        di = Container()
        
        @di.provider
        class MyClass(object):
            pass
        
        container = Container(di)
        container.get(MyClass)
    
    Created instances are scoped by container.
    """
    
    WRAPPER_ASSIGNMENTS = list(functools.WRAPPER_ASSIGNMENTS) + ["__self__", "im_self", "im_class"]
    
    def __init__(self, parent=None):
        super(Container, self).__init__()
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self._registry = {}
        self._instances = {}
        self._configurators = {"result":{}, "kwargs":{}}
        self.parent = parent
        
    def _di_init(self, f):
        @self._wraps(f)
        def wrapper(self, *args, **kwargs):
            self.__di__ = kwargs.pop("__di__", None)
            f(self, *args, **kwargs)
        return wrapper
    
    def _normalize(self, o):
        if inspect.isclass(o) or inspect.isfunction(o):
            return "%s.%s" % (o.__module__, o.__qualname__)
        
        if isinstance(o, str):
            return o
        
        raise Exception("Unknown object: %r" % o)
    
    def _wraps(self, wrapped):
        return functools.wraps(wrapped, assigned=self.WRAPPER_ASSIGNMENTS)
    
    def _is_related(self, di):
        if di is self:
            return True
        
        if self.parent:
            return self.parent._is_related(di)
        else:
            return False
    
    def _find_di(self, o, args=[], kwargs={}):
        try:
            o.__uses_di
        except:
            # remove only if no-DI aware method, other DI are ok
            di = kwargs.pop("__di__", None)
        else:
            # check if this is out instance, or related - if not, pass 
            if self._is_related(o.__uses_di):
                di = kwargs.get("__di__", None)
        
        if not di and args:
            try:
                di = args[0].__di__
            except:
                pass
        
        try:
            di = o.__di__
        except:
            pass
        
        return di
    
    def parameter(self, key, value):
        self._registry[self._normalize(key)] = value
    
    def params(self, **di_args):
        def wrapper(f):
            def inner(di, args, kwargs):
                if di:
                    for k,v in di_args.items():
                        kwargs.setdefault(k, di.get(v))
                return args, kwargs
            return self._di_wrap(f, False, cb=inner)
            
        return wrapper
    
    def property(self, f, *args, **kwargs):
        @functools.wraps(f)
        def wrapper(that):
            self.logger.debug("Using getter for %r from %r", f, that)
            di = self._find_di(that)
            if di:
                return di.get(f)
            else:
                return None
        return property(wrapper)
    
    def get_from_registry(self, k):
        if k in self._registry:
            return self._registry[k]
        if self.parent:
            return self.parent.get_from_registry(k)
        raise Exception("Object %r not registered" % k)
    
    def has(self, o):
        k = self._normalize(o)
        try:
            self.get_from_registry(k)
        except:
            return False
        else:
            return True
    
    def _configuration_pass(self, t, k, value):
        
        if self.parent:
            self.parent._configuration_pass(t, k, value)
        
        confs = self._configurators.get(t)
        if k in confs:
            for c in confs[k]:
                c(value)
    
    def get(self, k, args=[], kwargs={}):
        
        k = self._normalize(k)
        
        if k in self._instances:
            return self._instances[k]
        
        f = self.get_from_registry(k)
        
        if callable(f):
            self.logger.debug("Creating instance of %r", f)
            
            args = list(args)
            kwargs = dict(kwargs)
            
            self._configuration_pass("kwargs", k, kwargs)
            
            r = f(*args, __di__=self, **kwargs)
            self._instances[k] = r
            
            self._configuration_pass("result", k, r)
            
            return r
        else:
            return f
    
    def _di_wrap(self, m, register=True, cb = None):
        @self._wraps(m)
        def wrapper(*args, **kwargs):
            di = self._find_di(m, args, kwargs)
            
            if cb:
                args, kwargs = cb(di, args, kwargs)
            
            return m(*args, **kwargs)
        wrapper.__uses_di = self
        if register:
            self._registry[self._normalize(wrapper)] = wrapper
        
        return wrapper
    
    def provide_method(self, m):
        def wrapper(di, args, kwargs):
            cls_name = self._normalize(m).rsplit(".",1)[0]
            args = list(args)
            if self.has(cls_name):
                args.insert(0, di.get(cls_name))
            
            return args, kwargs
        
        return self._di_wrap(m, cb=wrapper)
    
    def provide_function(self, m):
        return self._di_wrap(m)
    
    def provide_class(self, cls):
        self._registry[self._normalize(cls)] = cls
        cls.__init__ = self._di_init(cls.__init__)
        return cls
    
    def _configurator_decorator(self, o, t):
        k = self._normalize(o)
        if not k in self._configurators[t]:
            self._configurators[t][k] = []
        def wrapper(f):
            self._configurators[t][k].append(f)
        return wrapper
    
    def configure_result(self, o):
        return self._configurator_decorator(o, "result")
    
    def configure_kwargs(self, o):
        return self._configurator_decorator(o, "kwargs")
    