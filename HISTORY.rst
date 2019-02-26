.. :changelog:

History
-------

v0.20.1 (2019-02-26)
....................
* fix type hints of ``parse_obj`` and similar methods, #405 by @erosennin
* fix submodel validation, #403 by @samuelcolvin
* correct type hints for ``ValidationError.json``, #406 by @layday

v0.20.0 (2019-02-18)
....................
* fix tests for python 3.8, #396 by @samuelcolvin
* Adds fields to the ``dir`` method for autocompletion in interactive sessions, #398 by @dgasmith
* support ``ForwardRef`` (and therefore ``from __future__ import annotations``) with dataclasses, #397 by @samuelcolvin

v0.20.0a1 (2019-02-13)
......................
* **breaking change** (maybe): more sophisticated argument parsing for validators, any subset of
  ``values``, ``config`` and ``field`` is now permitted, eg. ``(cls, value, field)``,
  however the variadic key word argument ("``**kwargs``") **must** be called ``kwargs``, #388 by @samuelcolvin
* **breaking change**: Adds ``skip_defaults`` argument to ``BaseModel.dict()`` to allow skipping of fields that
  were not explicitly set, signature of ``Model.construct()`` changed, #389 by @dgasmith
* add ``py.typed`` marker file for PEP-561 support, #391 by @je-l
* Fix ``extra`` behaviour for multiple inheritance/mix-ins, #394 by @YaraslauZhylko

v0.19.0 (2019-02-04)
....................
* Support ``Callable`` type hint, fix #279 by @proofit404
* Fix schema for fields with ``validator`` decorator, fix #375 by @tiangolo
* Add ``multiple_of`` constraint to ``ConstrainedDecimal``, ``ConstrainedFloat``, ``ConstrainedInt``
  and their related types ``condecimal``, ``confloat``, and ``conint`` #371, thanks @StephenBrown2
* Deprecated ``ignore_extra`` and ``allow_extra`` Config fields in favor of ``extra``, #352 by @liiight
* Add type annotations to all functions, test fully with mypy, #373 by @samuelcolvin
* fix for 'missing' error with ``validate_all`` or ``validate_always``, #381 by @samuelcolvin
* Change the second/millisecond watershed for date/datetime parsing to ``2e10``, #385 by @samuelcolvin

v0.18.2 (2019-01-22)
....................
* Fix to schema generation with ``Optional`` fields, fix #361 by @samuelcolvin

v0.18.1 (2019-01-17)
....................
* add ``ConstrainedBytes`` and ``conbytes`` types, #315 @Gr1N
* adding ``MANIFEST.in`` to include license in package ``.tar.gz``, #358 by @samuelcolvin

v0.18.0 (2019-01-13)
....................
* **breaking change**: don't call validators on keys of dictionaries, #254 by @samuelcolvin
* Fix validators with ``always=True`` when the default is ``None`` or the type is optional, also prevent
  ``whole`` validators being called for sub-fields, fix #132 by @samuelcolvin
* improve documentation for settings priority and allow it to be easily changed, #343 by @samuelcolvin
* fix ``ignore_extra=False`` and ``allow_population_by_alias=True``, fix #257 by @samuelcolvin
* **breaking change**: Set ``BaseConfig`` attributes ``min_anystr_length`` and ``max_anystr_length`` to
  ``None`` by default, fix #349 in #350 by @tiangolo
* add support for postponed annotations, #348 by @samuelcolvin

v0.17.0 (2018-12-27)
....................
* fix schema for ``timedelta`` as number, #325 by @tiangolo
* prevent validators being called repeatedly after inheritance, #327 by @samuelcolvin
* prevent duplicate validator check in ipython, fix #312 by @samuelcolvin
* add "Using Pydantic" section to docs, #323 by @tiangolo & #326 by @samuelcolvin
* fix schema generation for fields annotated as ``: dict``, ``: list``,
  ``: tuple`` and ``: set``, #330 & #335 by @nkonin
* add support for constrained strings as dict keys in schema, #332 by @tiangolo
* support for passing Config class in dataclasses decorator, #276 by @jarekkar
  (**breaking change**: this supersedes the ``validate_assignment`` argument with ``config``)
* support for nested dataclasses, #334 by @samuelcolvin
* better errors when getting an ``ImportError`` with ``PyObject``, #309 by @samuelcolvin
* rename ``get_validators`` to ``__get_validators__``, deprecation warning on use of old name, #338 by @samuelcolvin
* support ``ClassVar`` by excluding such attributes from fields, #184 by @samuelcolvin

v0.16.1 (2018-12-10)
....................
* fix ``create_model`` to correctly use the passed ``__config__``, #320 by @hugoduncan

v0.16.0 (2018-12-03)
....................
* **breaking change**: refactor schema generation to be compatible with JSON Schema and OpenAPI specs, #308 by @tiangolo
* add ``schema`` to ``schema`` module to generate top-level schemas from base models, #308 by @tiangolo
* add additional fields to ``Schema`` class to declare validation for ``str`` and numeric values, #311 by @tiangolo
* rename ``_schema`` to ``schema`` on fields, #318 by @samuelcolvin
* add ``case_insensitive`` option to ``BaseSettings`` ``Config``, #277 by @jasonkuhrt

v0.15.0 (2018-11-18)
....................
* move codebase to use black, #287 by @samuelcolvin
* fix alias use in settings, #286 by @jasonkuhrt and @samuelcolvin
* fix datetime parsing in ``parse_date``, #298 by @samuelcolvin
* allow dataclass inheritance, fix #293 by @samuelcolvin
* fix ``PyObject = None``, fix #305 by @samuelcolvin
* allow ``Pattern`` type, fix #303 by @samuelcolvin

v0.14.0 (2018-10-02)
....................
* dataclasses decorator, #269 by @Gaunt and @samuelcolvin

v0.13.1 (2018-09-21)
.....................
* fix issue where int_validator doesn't cast a ``bool`` to an ``int`` #264 by @nphyatt
* add deep copy support for ``BaseModel.copy()`` #249, @gangefors

v0.13.0 (2018-08-25)
.....................
* raise an exception if a field's name shadows an existing ``BaseModel`` attribute #242
* add ``UrlStr`` and ``urlstr`` types #236
* timedelta json encoding ISO8601 and total seconds, custom json encoders #247, by @cfkanesan and @samuelcolvin
* allow ``timedelta`` objects as values for properties of type ``timedelta`` (matches ``datetime`` etc. behavior) #247

v0.12.1 (2018-07-31)
....................
* fix schema generation for fields defined using ``typing.Any`` #237

v0.12.0 (2018-07-31)
....................
* add ``by_alias`` argument in ``.dict()`` and ``.json()`` model methods #205
* add Json type support #214
* support tuples #227
* major improvements and changes to schema #213

v0.11.2 (2018-07-05)
....................
* add ``NewType`` support #115
* fix ``list``, ``set`` & ``tuple`` validation #225
* separate out ``validate_model`` method, allow errors to be returned along with valid values #221

v0.11.1 (2018-07-02)
....................
* support Python 3.7 #216, thanks @layday
* Allow arbitrary types in model #209, thanks @oldPadavan

v0.11.0 (2018-06-28)
....................
* make ``list``, ``tuple`` and ``set`` types stricter #86
* **breaking change**: remove msgpack parsing #201
* add ``FilePath`` and ``DirectoryPath`` types #10
* model schema generation #190
* JSON serialisation of models and schemas #133

v0.10.0 (2018-06-11)
....................
* add ``Config.allow_population_by_alias`` #160, thanks @bendemaree
* **breaking change**: new errors format #179, thanks @Gr1N
* **breaking change**: removed ``Config.min_number_size`` and ``Config.max_number_size`` #183, thanks @Gr1N
* **breaking change**: correct behaviour of ``lt`` and ``gt`` arguments to ``conint`` etc. #188
  for the old behaviour use ``le`` and ``ge`` #194, thanks @jaheba
* added error context and ability to redefine error message templates using ``Config.error_msg_templates`` #183,
  thanks @Gr1N
* fix typo in validator exception #150
* copy defaults to model values, so different models don't share objects #154

v0.9.1 (2018-05-10)
...................
* allow custom ``get_field_config`` on config classes #159
* add ``UUID1``, ``UUID3``, ``UUID4`` and ``UUID5`` types #167, thanks @Gr1N
* modify some inconsistent docstrings and annotations #173, thanks @YannLuo
* fix type annotations for exotic types #171, thanks @Gr1N
* re-use type validators in exotic types #171
* scheduled monthly requirements updates #168
* add ``Decimal``, ``ConstrainedDecimal`` and ``condecimal`` types #170, thanks @Gr1N

v0.9.0 (2018-04-28)
...................
* tweak email-validator import error message #145
* fix parse error of ``parse_date()`` and ``parse_datetime()`` when input is 0 #144, thanks @YannLuo
* add ``Config.anystr_strip_whitespace`` and ``strip_whitespace`` kwarg to ``constr``,
  by default values is ``False`` #163, thanks @Gr1N
* add ``ConstrainedFloat``, ``confloat``, ``PositiveFloat`` and ``NegativeFloat`` types #166, thanks @Gr1N

v0.8.0 (2018-03-25)
...................
* fix type annotation for ``inherit_config`` #139
* **breaking change**: check for invalid field names in validators #140
* validate attributes of parent models #141
* **breaking change**: email validation now uses
  `email-validator <https://github.com/JoshData/python-email-validator>`_ #142

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
