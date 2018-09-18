# -*- coding: utf-8 -*-
'''Tests for package.

.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>

'''
import unittest

from glorpen.di import Container
from glorpen.di.scopes import ScopeSingleton, ScopePrototype
from glorpen.di.exceptions import ScopeWideningException,\
    UnknownServiceException, ServiceAlreadyCreated, RecursionException
from glorpen.di.container import Kwargs

class ImportableService(object):
    pass

class Test2(unittest.TestCase):
    
    def testConfigurator(self):
        c = Container()
        c.add_parameter('some.param', 'some_param')
        
        class MyConfigurator(object):
            def configure(self, o, param1):
                o.configured = True
                o.param1 = param1
            
            def configure_inject(self, o, param1):
                o.param_inject = param1
        
        class MyClass(object):
            
            configured = False
            param1 = None
            param_inject = None
            
        c.add_service(MyConfigurator)
        c.add_service(MyClass)\
            .configurator(service=MyConfigurator, method="configure", param1="param1")\
            .configurator(service=MyConfigurator, method="configure_inject", param1__param="some.param")\
        
        o = c.get(MyClass)
        self.assertTrue(o.configured, "configure constructor kwargs")
        self.assertEqual(o.param1, "param1", "pass parameter from configurator")
        self.assertEqual(o.param_inject, "some_param", "pass injected parameter from configurator")
    
    def testFactory(self):
    
        class CreatedClass(object):
            def __init__(self, string_a):
                super(CreatedClass, self).__init__()
                self.string_a = string_a
            
        class MyFactory(object):
            def get_my_instance(self, **kwargs):
                return CreatedClass(**kwargs)
    
        c = Container()
        
        c.add_service(MyFactory)
        c.add_service(CreatedClass)\
            .factory(service=MyFactory, method="get_my_instance")\
            .kwargs(string_a="a")
        
        o = c.get(CreatedClass)
        self.assertIsInstance(o, CreatedClass)
        self.assertEqual(o.string_a, "a", "factory method arguments")
    
    def testConstructorArguments(self):
        class MyClass(object):
            def __init__(self, o):
                super(MyClass, self).__init__()
                self.o = o
        c = Container()
        c.add_service(MyClass).kwargs(o="a")
        
        self.assertEqual(c.get(MyClass).o, "a")
    
    def testSingletonScope(self):
        class MyClass(object): pass
        
        c = Container()
        c.add_service(MyClass).scope(ScopeSingleton)
        
        self.assertIs(c.get(MyClass), c.get(MyClass), "instances are the same")
    
    def testPrototypeScope(self):
        class MyClass(object): pass
        
        c = Container()
        c.add_service(MyClass).scope(ScopePrototype)
        
        self.assertIsNot(c.get(MyClass), c.get(MyClass), "instances are not the same")
    
    def testScopeWidening(self):
        class MyClassA(object): pass
        class MyClassB(object):
            def __init__(self, a):
                super(MyClassB, self).__init__()
        
        c = Container()
        c.add_service(MyClassA).scope(ScopePrototype)
        c.add_service(MyClassB).scope(ScopeSingleton)\
            .kwargs(a__svc=MyClassA)
        
        with self.assertRaises(ScopeWideningException, msg="error on scope widening"):
            c.get(MyClassB)
    
    def testGettingNotExisitingService(self):
        c = Container()
        with self.assertRaises(UnknownServiceException):
            c.get(str)
    
    def testRecursion(self):
        c = Container()
        class MyClass(object): pass
        c.add_service(MyClass).kwargs(obj__svc=MyClass)
        with self.assertRaises(RecursionException, msg="throw exception when self referencing service is found"):
            c.get(MyClass)
    
    def testSetters(self):
        class MyClass(object):
            a="b"
        
        c = Container()
        c.add_service(MyClass).set(a="a")
        
        self.assertEqual(c.get(MyClass).a, "a")
    
    def testParameters(self):
        class MyClass(object):
            a="b"
        
        c = Container()
        c.add_parameter("a", "asd")
        c.add_service(MyClass).set(a__param="a")
        
        self.assertEqual(c.get(MyClass).a, "asd")
    
    def testServiceChanging(self):
        class MyClass(object): pass
        
        c = Container()
        svc = c.add_service(MyClass)
        
        svc.set(a="a")
        svc.set(b="b")
        svc.set(a="c")
        
        o = c.get(MyClass)
        self.assertEqual(o.a, "c")
        self.assertEqual(o.b, "b")
        
        with self.assertRaises(ServiceAlreadyCreated):
            svc.set(a="a")
    
    def testServiceWithImport(self):
        c = Container()
        c.add_service("glorpen.di.tests.python2.ImportableService")
        self.assertIsInstance(c.get(ImportableService), ImportableService)
    
    def testSelfService(self):
        c = Container()
        self.assertIs(c.get(Container), c)
    
    def testKwargs(self):
        class MyClass(object):
            a_param = b_param = None
            def a(self, param):
                self.a_param = param
            def b(self, param):
                self.b_param = param
        c = Container()
        svc = c.add_service(MyClass)
        svc.call("a", param="param1")
        svc.call("b", Kwargs(param="param2"))
        
        o = c.get(MyClass)
        
        self.assertEqual(o.a_param, "param1", "simple param")
        self.assertEqual(o.b_param, "param2", "kwargs helper param")
    
    def testAliases(self):
        c = Container()
        
        class MyClass(object):
            pass
        
        c.add_service(MyClass)
        c.add_alias(MyClass, 'alias-test')
        self.assertIsInstance(c.get('alias-test'), MyClass)
