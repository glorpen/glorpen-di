v1.5.0
------

- fixed error when passing string as service name upon creation
- added kwargs_modifiers to allow mangling service constructor params
- more tests

v1.4.1
------

- fixed compatibilitry with python2

v1.4.0
------

- readable exceptions
- updated namespace package code

v1.3.2
------

- version bump for ci

v1.3.1
------

- added service aliasing

v1.3.0
------

- [BC break] Service.configurator no longer accepts `callable_args` and `methods_args` parameters,
  you can now just inject required params. 
