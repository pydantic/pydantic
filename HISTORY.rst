.. :changelog:

History
-------

v0.7.1 (2018-02-07)
...................
* fix bug with ``create_model`` modifying the base class

v0.7.0 (2018-02-06)
...................
* added compatibility with abstract base classes (ABCs) #123
* add ``create_model`` method #113 #125
* **breaking change**: rename ``.config`` to ``.__config__`` on a model
* **breaking change**: remove deprecated ``.values()`` on a model, use ``.dict()`` instead
* remove use of ``OrderedDict`` and use simple dict #126
* add ``Config.use_enum_values`` #127
* add wildcard validators of the form ``@validate('*')`` #128

v0.6.4 (2018-02-01)
...................
* allow python date and times objects #122

v0.6.3 (2017-11-26)
...................
* fix direct install without ``README.rst`` present

v0.6.2 (2017-11-13)
...................
* errors for invalid validator use
* safer check for complex models in ``Settings``

v0.6.1 (2017-11-08)
...................
* prevent duplicate validators, #101
* add ``always`` kwarg to validators, #102

v0.6.0 (2017-11-07)
...................
* assignment validation #94, thanks petroswork!
* JSON in environment variables for complex types, #96
* add ``validator`` decorators for complex validation, #97
* depreciate ``values(...)`` and replace with ``.dict(...)``, #99

v0.5.0 (2017-10-23)
...................
* add ``UUID`` validation #89
* remove ``index`` and ``track`` from error object (json) if they're null #90
* improve the error text when a list is provided rather than a dict #90
* add benchmarks table to docs #91

v0.4.0 (2017-07-08)
...................
* show length in string validation error
* fix aliases in config during inheritance #55
* simplify error display
* use unicode ellipsis in ``truncate``
* add ``parse_obj``, ``parse_raw`` and ``parse_file`` helper functions #58
* switch annotation only fields to come first in fields list not last

v0.3.0 (2017-06-21)
...................
* immutable models via ``config.allow_mutation = False``, associated cleanup and performance improvement #44
* immutable helper methods ``construct()`` and ``copy()`` #53
* allow pickling of models #53
* ``setattr`` is removed as ``__setattr__`` is now intelligent #44
* ``raise_exception`` removed, Models now always raise exceptions #44
* instance method validators removed
* django-restful-framework benchmarks added #47
* fix inheritance bug #49
* make str type stricter so list, dict etc are not coerced to strings. #52
* add ``StrictStr`` which only always strings as input #52

v0.2.1 (2017-06-07)
...................
* pypi and travis together messed up the deploy of ``v0.2`` this should fix it

v0.2.0 (2017-06-07)
...................
* **breaking change**: ``values()`` on a model is now a method not a property,
  takes ``include`` and ``exclude`` arguments
* allow annotation only fields to support mypy
* add pretty ``to_string(pretty=True)`` method for models

v0.1.0 (2017-06-03)
...................
* add docs
* add history
