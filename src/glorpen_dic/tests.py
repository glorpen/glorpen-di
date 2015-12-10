'''
Created on 9 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import unittest

from glorpen_dic import Container
from glorpen_dic.scopes import ScopeSingleton, ScopePrototype
from glorpen_dic.exceptions import ScopeWideningException,\
    UnknownServiceException

class Test(unittest.TestCase):
    
    def testConfigurator(self):
        c = Container()
        
        class MyConfigurator(object):
            def configure(self, o):
                o.configured = True
            
            def configure_args(self, kwargs):
                kwargs["o"] = "configured o"
        
        class MyClass(object):
            
            configured = False
            
            def __init__(self, o):
                super(MyClass, self).__init__()
                self.o = o
            
            def is_configured(self):
                return self.configured
            
        c.add_service(MyConfigurator)
        c.add_service(MyClass)\
            .configurator(service=MyConfigurator, method="configure", args_method="configure_args")
        
        o = c.get(MyClass)
        self.assertEqual(o.o, "configured o", "configure object")
        self.assertTrue(o.is_configured(), "configure constructor kwargs")
    
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
    
if __name__ == "__main__":
    unittest.main()
