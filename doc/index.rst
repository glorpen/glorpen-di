=====================
Glorpen IOC Container
=====================

Another Dependency Injection library for Python.

This package has following three guidelines:

- any class configured by *Container* mechanism should not be modified in any way
- there is no need for external services definition files for *Container*
- no *Container* compiling and service tagging - we have introspection and dynamic language for this task

And so this package provides:

- **no** xml configuration
- **no** annotations (more cons than pros)
- **no** changes to services code

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

Contents
========

.. toctree::
   :maxdepth: 2
   
   code.rst
   usage.rst
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
