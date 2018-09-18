=====================
Glorpen IOC Container
=====================

.. image:: https://travis-ci.org/glorpen/glorpen-di.svg?branch=master

.. image:: https://readthedocs.org/projects/glorpen-di/badge/?version=latest

Another Dependency Injection library for Python.

This package has following three guidelines:

- any class configured by *Container* mechanism should not be modified in any way
- there is no need for external services definition files for *Container*
- no *Container* compiling and service tagging - we have introspection and dynamic language for this task

And so this package provides:

- **no** xml configuration
- **no** annotations (more cons than pros)
- **no** changes to services code

Official repositories
=====================

For forking and other funnies.

BitBucket: https://bitbucket.org/glorpen/glorpen-di

GitHub: https://github.com/glorpen/glorpen-di


Supported design patterns
=========================

Service instance can be created by:

- factory service
- calling class object with arguments

Instance options can be altered by:

- constructor arguments
- setters
- calling methods
- using configurator service

Each service has defined scope, service cannot request other service from narrower scope.

Injecting services and parameters
=================================

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



**See https://glorpen-di.readthedocs.io/en/latest/ for code examples and more documentation.**
