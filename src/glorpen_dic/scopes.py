'''
Created on 10 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

class ScopeBase(object):
    def get(self, c, name):
        raise NotImplementedError()

class ScopePrototype(ScopeBase):
    def get(self, c, name):
        return c()

class ScopeSingleton(ScopeBase):
    
    def __init__(self):
        super(ScopeSingleton, self).__init__()
        self.instances = {}
    
    def get(self, creator, name):
        if not name in self.instances:
            self.instances[name] = creator()
        return self.instances[name]
