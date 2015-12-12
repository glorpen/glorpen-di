'''
Created on 9 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import unittest

from glorpen_dic import Container

class Test(unittest.TestCase):
    
    def testSimpleKeysAndValues(self):
        c = Container()
        
        d = {
            "string": "value",
            "integer": 3,
            "dict": {"A":1}
        }
        
        for k,v in d.items():
            c.parameter(k, v)
            self.assertIs(c.get(k), v)
    
    def testClasses(self):
        c = Container()
        
        @c.provide_class
        class MyClass(object):
            pass
        
        self.assertIsInstance(c.get(MyClass), MyClass)
    
    def testParams(self):
        c = Container()
        c.parameter("string", "a")
        
        @c.provide_class
        class MyClass(object):
            @c.params(a="string")
            def __init__(self, a):
                super(MyClass, self).__init__()
                self.a = a
            
            @c.params(a="string")
            def method(self, a):
                return a, self.a
            
        self.assertIsInstance(c.get(MyClass), MyClass)
        self.assertEqual(c.get(MyClass).method(), ("a", "a"))
    
    def testProperty(self):
        c= Container()
        
        c.parameter("string1", "a")
        c.parameter("string2", "b")
        
        @c.provide_class
        class Producer(object):
            
            prop = c.property("string1")
            
            @c.params(init_value="string1")
            def __init__(self, init_value):
                super(Producer, self).__init__()
                self.init_value = init_value
            
            @c.params(v="string2")
            def p(self, v):
                return self.init_value, v
            
        Producer("a").p("q")
        self.assertEqual(c.get(Producer).p(), ('a','b'))
        self.assertEqual(c.get(Producer).prop, "a")
    
    def testMethodProvider(self):
        c = Container()
        
        @c.provide_class
        class Producer(object):
            @c.provide_method
            def p(self):
                return "q"
        
        self.assertEqual(c.get(Producer.p), "q")
    
    def testFunctionProvider(self):
        c = Container()
        
        @c.provide_function
        def f():
            return "a"
        
        self.assertEqual(c.get(f), "a")
    
    def testResultConfigurator(self):
        c = Container()
        
        @c.provide_function
        def f():
            return {}
        
        @c.configure_result(f)
        def configure(res):
            res["a"]="a"
        
        self.assertEqual(c.get(f), {"a":"a"})
    
    def testArgsConfigurator(self):
        c = Container()
        
        @c.provide_function
        def f(a="a"):
            return a
        
        @c.configure_kwargs(f)
        def configure(kwargs):
            kwargs["a"] = "b"
        
        self.assertEqual(c.get(f), "b")
    
    def multipleDis(self):
        a = Container()
        a.parameter("string", "a")
        b = Container()
        b.parameter("string", "b")
        
        @a.provide_function
        @b.provide_function
        @a.params(v="string")
        @b.params(v="string")
        def f(v):
            return v
        
        self.assertEqual(a.get(f), "a")
        self.assertEqual(b.get(f), "b")

if __name__ == "__main__":
    unittest.main()
