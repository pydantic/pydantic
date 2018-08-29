.. :changelog:

History
-------

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
