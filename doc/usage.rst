Usage examples
**************

Injecting services and parameters
---------------------------------

.. code-block:: python

   from glorpen.di import Container
   
   class MyParamService(object):
       pass
   
   class MyService(object):
       def __init__(self, obj, text, value):
           super(MyService, self).__init__()
           print("service instance: %s" % obj)
           print("container parameter: %s" % text)
           print("provided value: %s" % value)
       
   c = Container()
   
   c.add_service(MyParamService)
   c.add_parameter('my-param', "value from container")
   c.add_service(MyService).kwargs(obj__svc=MyParamService, text__param="my-param", value="defined value")
   
   c.get(MyService)

Running snippet will print:

::

   service instance: <__main__.MyParamService object at 0x7f2fef6e9828>
   container parameter: value from container
   provided value: defined value

Arguments
---------

In cases when you want to use inject parameter already used by internal methods, eg. :meth:`glorpen.di.container.Service.call`,
you can pass args with :class:`glorpen.di.container.Kwargs` helper class.

.. code-block:: python

   svc.configurator(callable=configurator, kwargs=Kwargs(router__svc=Router), other_param="param")
   svc.call("some_method", kwargs=Kwargs(router__svc=Router), other_param="param")

Arguments defined by :class:`glorpen.di.container.Kwargs` are overriding ones provided by `**kwargs` notation. 

Configurators
-------------

Configurators are services or callables used to configure main service.
Provided callables are given main service instance as first argument.

.. code-block:: python

   def configurator(obj, some_service):
      obj.some_thing = some_service()
   svc.configurator(callable=configurator, some_service__svc=MyClass)
   svc.configurator(service=ConfiguratorClass, method="some_method", some_service__svc=MyClass)

Factories
---------

Services that create other objects. It is possible to provide parameters/other services from Container to given callables.

.. code-block:: python

   def factory(some_service):
      return some_service("arg1")
   svc1.factory(callable=factory, some_service__svc=MyClass)
   
   class FactoryClass(object):
      def create_new(self, some_service):
      return some_service("arg1")
   svc2.factory(service=FactoryClass, method="create_new", some_service__svc=MyClass)

Calling methods and settings properties
---------------------------------------

To call method on service creation:

.. code-block:: python

   svc.call("some_method", some_service__svc=MyClass)

To set properties on service creation:

.. code-block:: python

   svc.set(my_prop__svc=MyClass)

Using type hints for auto injection
***********************************

Sometimes it is easier to just auto-fill function arguments, when using Python3 it can be done by arguments type hinting (see :mod:`typing` for more information).

You can enable function hints lookup by using :meth:`glorpen.di.container.Service.kwargs_from_signature` for constructor arguments
and :meth:`glorpen.di.container.Service.call_with_signature` for methods.

.. code-block:: python

   from glorpen.di import Container
   
   class MyParamService(object):
       pass
   
   class MyService(object):
       def __init__(self, param:MyParamService):
           super(MyService, self).__init__()
           print("MyService.__init__: %s" % param.__class__.__name__)
       
       def some_method(self, param:MyParamService):
           print("MyService.some_method: %s" % param.__class__.__name__)
           
   c = Container()
   
   c.add_service(MyParamService)
   c.add_service(MyService).kwargs_from_signature().call_with_signature("some_method")
   
   print("Continer.get: %s" % c.get(MyService).__class__.__name__)

Snippet will create following output:

::

   MyService.__init__: MyParamService
   MyService.some_method: MyParamService
   Continer.get: MyService



Adding custom scope
*******************

You can define new scope by extending :class:`glorpen.di.scopes.ScopeBase`
and using :meth:`glorpen.di.container.Container.set_scope_hierarchy`.

.. code-block:: python

   from glorpen.di.scopes import ScopePrototype, ScopeSingleton, ScopeBase
   from random import randint
   
   class RandomScope(ScopeBase):
       """Returns new or cached instances based on random factor."""
       def __init__(self, randomity=3):
           super(RandomScope, self).__init__()
           self.rnd = randomity
           self.instances = {}
      
       def get(self, creator, name):
           if not name in self.instances or randint(0, self.rnd) == 0:
               self.instances[name] = creator()
           return self.instances[name]
   
   c = Container()
   
   # add scope with parameter
   c.set_scope_hierarchy(ScopeSingleton, RandomScope(5), ScopePrototype)
   
   # configure "str" service so we can see instances count
   counter = 0
   def configurator(kwargs):
       global counter
       kwargs.setdefault("object", "instance number: %d" % counter)
       counter+=1
   
   c.add_service('arg.test').implementation(str)\
       .configurator(args_callable=configurator)\
       .scope(RandomScope)
   
   for i in range(0,10):
       print(c.get("arg.test"))


Running script will print:

::

   instance number: 0
   instance number: 0
   instance number: 0
   instance number: 0
   instance number: 1
   instance number: 2
   instance number: 2
   instance number: 3
   instance number: 4
   instance number: 4
