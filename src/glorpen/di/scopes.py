# -*- coding: utf-8 -*-
'''Built-in scopes.

.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>

'''

class ScopeBase(object):
    """Base class for all scopes."""
    def get(self, c, name):
        raise NotImplementedError()

class ScopePrototype(ScopeBase):
    """Scope that creates new instance of given service each time it is requested."""
    def get(self, c, name):
        return c()

class ScopeSingleton(ScopeBase):
    """Scope that creates instance of given service only once."""
    
    def __init__(self):
        super(ScopeSingleton, self).__init__()
        self.instances = {}
    
    def get(self, creator, name):
        if not name in self.instances:
            self.instances[name] = creator()
        return self.instances[name]
