'''
Created on 20 cze 2015

@author: Arkadiusz Dzięgiel
'''
import functools
import inspect
import itertools
import logging

class DI(object):
    
    def __init__(self):
        super(DI, self).__init__()
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self._registry = {}
        self._instances = {}
    
    def get(self, k, args=[], kwargs={}):
        k = self._normalize(k)
        
        if k in self._instances:
            return self._instances[k]
        
        if k in self._registry:
            f = self._registry[k]
            if callable(f):
                self.logger.debug("Creating instance of %r", f)
                r = f(*args, **kwargs)
                self._instances[k] = r
                return r
            else:
                return f
        else:
            raise Exception("Object %r not registered" % k)
    
    def _normalize(self, f):
        if inspect.ismethod(f):
            return f.__func__
        if isinstance(f, type):
            return f
        if hasattr(f, '__class__'):
            return f.__class__
        return f
    
    def provider(self, f, key=None):
        kf = self._normalize(key or f)
        self._registry[kf] = f
        return f
    
    def params(self, *iargs, **ikwargs):
        def decorator(f):
            
            arg_names = inspect.getargspec(f).args
            
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                self.logger.debug("Injecting to %r", f)
                kwargs.update(zip(arg_names, args))
                
                for k,v in itertools.chain(zip(arg_names, iargs), ikwargs.items()):
                    kwargs.setdefault(k, self.get(v))
                
                return f(**kwargs)
            return wrapper
        return decorator
    
    def property(self, f, *args, **kwargs):
        @functools.wraps(f)
        def wrapper(cls):
            self.logger.debug("Using getter for %r from %r", f, cls)
            return self.get(f, args, kwargs)
        return property(wrapper)
    

inject = DI()

if __name__ == "__main__":
    
    class Test(object):
        pass
    
    t = Test()
    inject.provider(t)
    
    print(inject.get(Test))
    
    
    @inject.provider
    def get_connection(asd):
        return "qwe"
    
    class Backend(object):
        def __init__(self):
            super(Backend, self).__init__()
            inject.provider(self.get_connection)
        def get_connection(self):
            return "connection"
    
    q=Backend()
    
    print(inject.get(Backend.get_connection))
    print(inject.get(get_connection, "q"))
    
    @inject.provider
    class Backend(object):
        @inject.provider
        def get_connection(self):
            return "connection"
    
    @inject.provider
    class Cache(object):
        backend = inject.property(Backend)
    
    @inject.params(cache=Cache)
    def a(cache=None, q=2, x=None):
        print(cache,q,x)
    
    @inject.params(cache=Cache)
    def b(cache,q=3,x=None):
        print(cache,q,x)
    
    @inject.params(Cache)
    def c(cache):
        print(cache.backend)
    
    inject.provider("asd", key="test")
    
    @inject.params(q="test")
    def d(q):
        print(q)
    
    a('a')
    a(cache='a')
    a()
    b('b')
    b(cache='b')
    b()
    c()
    d()
