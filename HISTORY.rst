.. :changelog:

History
-------

v0.3.0 (TBC)
............
* immutable models via ``config.allow_mutation = False``, associated cleanup and performance improvement #44
* immutable helper methods ``construct()`` and ``copy()`` #53
* ``setattr`` is removed as ``__setattr__`` is now intelligent #44
* ``raise_exception`` removed, Models now always raise exceptions #44
* instance method validators removed TODO
* django-restful-framework benchmarks added #47
* fix inheritance bug #49

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
