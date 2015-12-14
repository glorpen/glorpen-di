# -*- coding: utf-8 -*-
'''Tests for package.

.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>

'''
import unittest

from glorpen.di import Container

class Test3(unittest.TestCase):
    
    def testSignature(self):
        c = Container()
        
        class ParamClass(object): pass
        class MyClass(object):
            t = None
            m = None
            def __init__(self, t: ParamClass, a: str=None):
                super(MyClass, self).__init__()
                self.t = t
            
            def method(self, t: ParamClass):
                self.m = t
        
        c.add_service(ParamClass)
        c.add_service(MyClass)\
            .kwargs_from_signature()\
            .call_with_signature("method")
        
        self.assertIsInstance(c.get(MyClass).t, ParamClass)
        self.assertIsInstance(c.get(MyClass).m, ParamClass)
