pydantic
========

.. toctree::
   :maxdepth: 2

|pypi| |license|

Current Version: |version|

Data validation and settings management using python type hinting.

Define how data should be in pure, canonical python; validate it with *pydantic*.

`PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_ introduced type hinting into python 3.5,
`PEP 526 <https://www.python.org/dev/peps/pep-0526/>`_ extended that with syntax for variable annotation in python 3.6.

*pydantic* uses those annotations to validate that untrusted data takes the form you want.

There's also support for an extension to `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_
where the input data is validated.

Example:

.. literalinclude:: examples/example1.py

(This script is complete, it should run "as is")

What's going on here:

* ``id`` is of type int; the annotation only declaration tells *pydantic* that this field is required. Strings,
  bytes or floats will be coerced to ints if possible, otherwise an exception would be raised.
* ``name`` is inferred as a string from the default, it is not required as it has a default.
* ``signup_ts`` is a datetime field which is not required (``None`` if it's not supplied), pydantic will process
  either a unix timestamp int (e.g. ``1496498400``) or a string representing the date & time.
* ``friends`` uses python's typing system, it is required to be a list of integers, as with ``id`` integer-like objects
  will be converted to integers.

If validation fails pydantic with raise an error with a breakdown of what was wrong:

.. literalinclude:: examples/example2.py

Rationale
---------

So *pydantic* uses some cool new language feature, but why should I actually go and use it?

**no brainfuck**
    no new schema definition micro-language to learn. If you know python (and perhaps skim read the
    `type hinting docs <https://docs.python.org/3/library/typing.html>`_) you know how to use *pydantic*.

**plays nicely with your IDE/linter/brain**
    because *pydantic* data structures are just instances of classes you define; auto-completion, linting,
    :ref:`mypy <usage_mypy>` and your intuition should all work properly with your validated data.

**dual use**
    *pydantic's* :ref:`BaseSettings <settings>` class allows it to be used in both a "validate this request data"
    context and "load my system settings" context. The main difference being that system settings can have defaults
    changed by environment variables and more complex objects like DSNs and python objects are often required.

**fast**
    In :ref:`benchmarks <benchmarks_tag>` *pydantic* is faster than all other tested libraries.

**validate complex structures**
    use of recursive *pydantic* models, ``typing``'s ``List`` and ``Dict`` etc. and validators allow
    complex data schemas to be clearly and easily defined and then checked.

**extensible**
    *pydantic* allows custom data types to be defined or you can extend validation with methods on a model decorated
    with the ``validator`` decorator.


Install
-------

Just::

    pip install pydantic

*pydantic* has no required dependencies except python 3.6 or 3.7 (and the dataclasses package in python 3.6).
If you've got python 3.6 and ``pip`` installed - you're good to go.

*pydantic* can optionally be compiled with `cython <https://cython.org/>`_ which should give a 30-50% performance
improvement. ``manylinux`` binaries exist for python 3.6 and 3.7, so if you're installing from PyPI on linux, you
should get *pydantic* compiled with no extra work. If you're installing manually, install ``cython`` before installing
*pydantic* and you should get *pydandic* compiled. Compilation with cython is not tested on windows or mac.
`[issue] <https://github.com/samuelcolvin/pydantic/issues/555>`_

To test if *pydantic* is compiled run::

    import pydantic
    print('compiled:', pydantic.compiled)

If you want *pydantic* to parse json faster you can add `ujson <https://pypi.python.org/pypi/ujson>`_
as an optional dependency. Similarly *pydantic's* email validation relies on
`email-validator <https://github.com/JoshData/python-email-validator>`_ ::

    pip install pydantic[ujson]
    # or
    pip install pydantic[email]
    # or just
    pip install pydantic[ujson,email]

Of course you can also install these requirements manually with ``pip install ...``.

Pydantic is also available on `conda <https://www.anaconda.com>`_ under the `conda-forge <https://conda-forge.org>`_ channel::

    conda install pydantic -c conda-forge

Usage
-----

PEP 484 Types
.............

*pydantic* uses ``typing`` types to define more complex objects.

.. literalinclude:: examples/ex_typing.py

(This script is complete, it should run "as is")

dataclasses
...........

.. note::

   New in version ``v0.14``.

If you don't want to use pydantic's ``BaseModel`` you can instead get the same data validation on standard
`dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ (introduced in python 3.7).

Dataclasses work in python 3.6 using the `dataclasses backport package <https://github.com/ericvsmith/dataclasses>`_.

.. literalinclude:: examples/ex_dataclasses.py

(This script is complete, it should run "as is")

You can use all the standard pydantic field types and the resulting dataclass will be identical to the one
created by the standard library ``dataclass`` decorator.

``pydantic.dataclasses.dataclass``'s arguments are the same as the standard decorator, except one extra
key word argument ``config`` which has the same meaning as :ref:`Config <config>`.

.. note::

   As a side effect of getting pydantic dataclasses to play nicely with mypy the ``config`` argument will show
   as invalid in IDEs and mypy, use ``@dataclass(..., config=Config) # type: ignore`` as a workaround. See
   `python/mypy#6239 <https://github.com/python/mypy/issues/6239>`_ for an explanation of why this is.

Nested dataclasses
~~~~~~~~~~~~~~~~~~

Since version ``v0.17`` nested dataclasses are supported both in dataclasses and normal models.

.. literalinclude:: examples/ex_nested_dataclasses.py

(This script is complete, it should run "as is")

Dataclasses attributes can be populated by tuples, dictionaries or instances of that dataclass.

Choices
.......

*pydantic* uses python's standard ``enum`` classes to define choices.

.. literalinclude:: examples/choices.py

(This script is complete, it should run "as is")

Validators
..........

Custom validation and complex relationships between objects can achieved using the ``validator`` decorator.

.. literalinclude:: examples/validators_simple.py

(This script is complete, it should run "as is")

A few things to note on validators:

* validators are "class methods", the first value they receive here will be the ``UserModel`` not an instance
  of ``UserModel``
* their signature can be ``(cls, value)`` or ``(cls, value, values, config, field)``. As of **v0.20**, any subset of
  ``values``, ``config`` and ``field`` is also permitted, eg. ``(cls, value, field)``, however due to the way
  validators are inspected, the variadic key word argument ("``**kwargs``") **must** be called ``kwargs``.
* validator should either return the new value or raise a ``ValueError`` or ``TypeError``
* where validators rely on other values, you should be aware that:

  - Validation is done in the order fields are defined, eg. here ``password2`` has access to ``password1``
    (and ``name``), but ``password1`` does not have access to ``password2``. You should heed the warning
    :ref:`below <usage_mypy_required>` regarding field order and required fields.

  - If validation fails on another field (or that field is missing) it will not be included in ``values``, hence
    ``if 'password1' in values and ...`` in this example.


.. note::

   From ``v0.18`` onwards validators are not called on keys of dictionaries. If you wish to validate keys,
   use ``whole`` (see below).


Pre and Whole Validators
~~~~~~~~~~~~~~~~~~~~~~~~

Validators can do a few more complex things:

.. literalinclude:: examples/validators_pre_whole.py

(This script is complete, it should run "as is")

A few more things to note:

* a single validator can apply to multiple fields, either by defining multiple fields or by the special value ``'*'``
  which means that validator will be called for all fields.
* the keyword argument ``pre`` will cause validators to be called prior to other validation
* the ``whole`` keyword argument will mean validators are applied to entire objects rather than individual values
  (applies for complex typing objects eg. ``List``, ``Dict``, ``Set``)

Validate Always
~~~~~~~~~~~~~~~

For performance reasons by default validators are not called for fields where the value is not supplied.
However there are situations where it's useful or required to always call the validator, e.g.
to set a dynamic default value.

.. literalinclude:: examples/validators_always.py

(This script is complete, it should run "as is")

You'll often want to use this together with ``pre`` since otherwise the with ``always=True``
*pydantic* would try to validate the default ``None`` which would cause an error.

Dataclass Validators
~~~~~~~~~~~~~~~~~~~~

Validators also work in Dataclasses.

.. literalinclude:: examples/validators_dataclass.py

(This script is complete, it should run "as is")

Field Checks
~~~~~~~~~~~~

On class creation validators are checked to confirm that the fields they specify actually exist on the model.

Occasionally however this is not wanted: when you define a validator to validate fields on inheriting models.
In this case you should set ``check_fields=False`` on the validator.

.. _recursive_models:

Recursive Models
................

More complex hierarchical data structures can be defined using models as types in annotations themselves.

The ellipsis ``...`` just means "Required" same as annotation only declarations above.

.. literalinclude:: examples/recursive.py

(This script is complete, it should run "as is")

.. _self_ref_models:

Self-referencing Models
~~~~~~~~~~~~~~~~~~~~~~~

Data structures with self-referencing models are also supported, provided the function
``update_forward_refs()`` is called once the model is created (you will be reminded
with a friendly error message if you don't).

Within the model, you can refer to the not-yet-constructed model by a string :

.. literalinclude:: examples/self_referencing_string.py

(This script is complete, it should run "as is")

You can also refer it by its type, provided you import ``annotations`` (see
:ref:`the relevant paragraph <postponed_annotations>` for support depending on Python
and pydantic versions).

.. literalinclude:: examples/self_referencing_annotations.py

(This script is complete, it should run "as is")

.. _schema:

Schema Creation
...............

*Pydantic* allows auto creation of JSON Schemas from models:

.. literalinclude:: examples/schema1.py

(This script is complete, it should run "as is")

Outputs:

.. literalinclude:: examples/schema1.json

The generated schemas are compliant with the specifications:
`JSON Schema Core <https://json-schema.org/latest/json-schema-core.html>`__,
`JSON Schema Validation <https://json-schema.org/latest/json-schema-validation.html>`__ and
`OpenAPI <https://github.com/OAI/OpenAPI-Specification>`__.

``BaseModel.schema`` will return a dict of the schema, while ``BaseModel.schema_json`` will return a JSON string
representation of that.

Sub-models used are added to the ``definitions`` JSON attribute and referenced, as per the spec.

All sub-models (and their sub-models) schemas are put directly in a top-level ``definitions`` JSON key for easy re-use
and reference.

"sub-models" with modifications (via the ``Schema`` class) like a custom title, description or default value,
are recursively included instead of referenced.

The ``description`` for models is taken from the docstring of the class or the argument ``description`` to
the ``Schema`` class.

Optionally the ``Schema`` class can be used to provide extra information about the field and validations, arguments:

* ``default`` (positional argument), since the ``Schema`` is replacing the field's default, its first
  argument is used to set the default, use ellipsis (``...``) to indicate the field is required
* ``alias`` - the public name of the field
* ``title`` if omitted ``field_name.title()`` is used
* ``description`` if omitted and the annotation is a sub-model, the docstring of the sub-model will be used
* ``const`` this field *must* take it's default value if it is present
* ``gt`` for numeric values (``int``, ``float``, ``Decimal``), adds a validation of "greater than" and an annotation
  of ``exclusiveMinimum`` to the JSON Schema
* ``ge`` for numeric values, adds a validation of "greater than or equal" and an annotation of ``minimum`` to the
  JSON Schema
* ``lt`` for numeric values, adds a validation of "less than" and an annotation of ``exclusiveMaximum`` to the
  JSON Schema
* ``le`` for numeric values, adds a validation of "less than or equal" and an annotation of ``maximum`` to the
  JSON Schema
* ``multiple_of`` for numeric values, adds a validation of "a multiple of" and an annotation of ``multipleOf`` to the
  JSON Schema
* ``min_length`` for string values, adds a corresponding validation and an annotation of ``minLength`` to the
  JSON Schema
* ``max_length`` for string values, adds a corresponding validation and an annotation of ``maxLength`` to the
  JSON Schema
* ``regex`` for string values, adds a Regular Expression validation generated from the passed string and an
  annotation of ``pattern`` to the JSON Schema
* ``**`` any other keyword arguments (eg. ``examples``) will be added verbatim to the field's schema

Instead of using ``Schema``, the ``fields`` property of :ref:`the Config class <config>` can be used
to set all the arguments above except ``default``.

The schema is generated by default using aliases as keys, it can also be generated using model
property names not aliases with ``MainModel.schema/schema_json(by_alias=False)``.

Types, custom field types, and constraints (as ``max_length``) are mapped to the corresponding
`JSON Schema Core <http://json-schema.org/latest/json-schema-core.html#rfc.section.4.3.1>`__ spec format when there's
an equivalent available, next to `JSON Schema Validation <http://json-schema.org/latest/json-schema-validation.html>`__,
`OpenAPI Data Types <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types>`__
(which are based on JSON Schema), or otherwise use the standard ``format`` JSON field to define Pydantic extensions
for more complex ``string`` sub-types.

The field schema mapping from Python / Pydantic to JSON Schema is done as follows:

.. include:: .tmp_schema_mappings.rst


You can also generate a top-level JSON Schema that only includes a list of models and all their related
submodules in its ``definitions``:

.. literalinclude:: examples/schema2.py

(This script is complete, it should run "as is")

Outputs:

.. literalinclude:: examples/schema2.json

You can customize the generated ``$ref`` JSON location, the definitions will still be in the key ``definitions`` and
you can still get them from there, but the references will point to your defined prefix instead of the default.

This is useful if you need to extend or modify JSON Schema default definitions location, e.g. with OpenAPI:

.. literalinclude:: examples/schema3.py

(This script is complete, it should run "as is")

Outputs:

.. literalinclude:: examples/schema3.json


Error Handling
..............

*Pydantic* will raise ``ValidationError`` whenever it finds an error in the data it's validating.

.. note::

   Validation code should not raise ``ValidationError`` itself, but rather raise ``ValueError`` or ``TypeError``
   (or subclasses thereof) which will be caught and used to populate ``ValidationError``.

One exception will be raised regardless of the number of errors found, that ``ValidationError`` will
contain information about all the errors and how they happened.

You can access these errors in a several ways:

:e.errors(): method will return list of errors found in the input data.
:e.json(): method will return a JSON representation of ``errors``.
:str(e): method will return a human readable representation of the errors.

Each error object contains:

:loc: the error's location as a list, the first item in the list will be the field where the error occurred,
   subsequent items will represent the field where the error occurred
   in :ref:`sub models <recursive_models>` when they're used.
:type: a unique identifier of the error readable by a computer.
:msg: a human readable explanation of the error.
:ctx: an optional object which contains values required to render the error message.

To demonstrate that:

.. literalinclude:: examples/errors1.py

(This script is complete, it should run "as is". ``json()`` has ``indent=2`` set by default, but I've tweaked the
JSON here and below to make it slightly more concise.)

In your custom data types or validators you should use ``TypeError`` and ``ValueError`` to raise errors:

.. literalinclude:: examples/errors2.py

(This script is complete, it should run "as is")

You can also define your own error class with abilities to specify custom error code, message template and context:

.. literalinclude:: examples/errors3.py

(This script is complete, it should run "as is")

datetime Types
...............

*Pydantic* supports the following `datetime <https://docs.python.org/library/datetime.html#available-types>`__
types:

* ``datetime`` fields can be:

  * ``datetime``, existing ``datetime`` object
  * ``int`` or ``float``, assumed as Unix time, e.g. seconds (if <= ``2e10``) or milliseconds (if > ``2e10``) since 1 January 1970
  * ``str``, following formats work:

    * ``YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z[±]HH[:]MM]]]``
    * ``int`` or ``float`` as a string (assumed as Unix time)

* ``date`` fields can be:

  * ``date``, existing ``date`` object
  * ``int`` or ``float``, see ``datetime``
  * ``str``, following formats work:

    * ``YYYY-MM-DD``
    * ``int`` or ``float``, see ``datetime``

* ``time`` fields can be:

  * ``time``, existing ``time`` object
  * ``str``, following formats work:

    * ``HH:MM[:SS[.ffffff]]``

* ``timedelta`` fields can be:

  * ``timedelta``, existing ``timedelta`` object
  * ``int`` or ``float``, assumed as seconds
  * ``str``, following formats work:

    * ``[-][DD ][HH:MM]SS[.ffffff]``
    * ``[±]P[DD]DT[HH]H[MM]M[SS]S`` (ISO 8601 format for timedelta)


.. literalinclude:: examples/datetime_example.py


Exotic Types
............

*Pydantic* comes with a number of utilities for parsing or validating common objects.

.. literalinclude:: examples/exotic.py

(This script is complete, it should run "as is")

Fields can also be of type ``Callable``:

.. literalinclude:: examples/callable.py

(This script is complete, it should run "as is")

.. warning::

    Callable fields only perform a simple check that the argument is
    callable, no validation of arguments, their types or the return
    type is performed.

Color Type
..........

You can use the ``Color`` data type for storing colors as per
`CSS3 specification <http://www.w3.org/TR/css3-color/#svg-color>`_. Color can be defined via:

- `name <http://www.w3.org/TR/SVG11/types.html#ColorKeywords>`_ (e.g. ``"Black"``, ``"azure"``)
- `hexadecimal value <https://en.wikipedia.org/wiki/Web_colors#Hex_triplet>`_
  (e.g. ``"0x000"``, ``"#FFFFFF"``, ``"7fffd4"``)
- RGB/RGBA tuples (e.g. ``(255, 255, 255)``, ``(255, 255, 255, 0.5)``
- `RGB/RGBA strings <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#RGB_colors>`_
  (e.g. ``"rgb(255, 255, 255)"`` or ``"rgba(255, 255, 255, 0.5)"``)
- `HSL strings <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#HSL_colors>`_
  (e.g. ``"hsl(270, 60%, 70%)"`` or ``"hsl(270, 60%, 70%, .5)"``)

.. literalinclude:: examples/ex_color_type.py

(This script is complete, it should run "as is")

``Color`` has the following methods:

:original: the original string or tuple passed to ``Color``
:as_named: returns a named CSS3 color, fails if the alpha channel is set or no such color exists unless
  ``fallback=True`` is supplied when it falls back to ``as_hex``
:as_hex: string in the format ``#ffffff`` or ``#fff``, can also be a 4 or 8 hex values if the alpha channel is set,
  e.g. ``#7f33cc26``
:as_rgb: string in the format ``rgb(<red>, <green>, <blue>)`` or ``rgba(<red>, <green>, <blue>, <alpha>)``
  if the alpha channel is set
:as_rgb_tuple: returns a 3- or 4-tuple in RGB(a) format, the ``alpha`` keyword argument can be used to define whether
  the alpha channel should be included,
  options: ``True`` - always include, ``False`` - never include, ``None`` (the default) - include if set
:as_hsl: string in the format ``hsl(<hue deg>, <saturation %>, <lightness %>)``
  or ``hsl(<hue deg>, <saturation %>, <lightness %>, <alpha>)`` if the alpha channel is set
:as_hsl_tuple: returns a 3- or 4-tuple in HSL(a) format, the ``alpha`` keyword argument can be used to define whether
  the alpha channel should be included,
  options: ``True`` - always include, ``False`` - never include, ``None`` (the default)  - include if set

The ``__str__`` method for ``Color`` returns ``self.as_named(fallback=True)``.

.. note::

   the ``as_hsl*`` refer to hue, saturation, lightness "HSL" as used in html and most of the world, **not**
   "HLS" as used in python's ``colorsys``.

Secret Types
............

You can use the ``SecretStr`` and the ``SecretBytes`` data types for storing sensitive information
that you do not want to be visible in logging or tracebacks.
The SecretStr and SecretBytes will be formatted as either `'**********'` or `''` on conversion to json.

.. literalinclude:: examples/ex_secret_types.py

(This script is complete, it should run "as is")

Json Type
.........

You can use ``Json`` data type - *Pydantic* will first parse raw JSON string and then will validate parsed object
against defined Json structure if it's provided.

.. literalinclude:: examples/ex_json_type.py

(This script is complete, it should run "as is")

Custom Data Types
.................

You can also define your own data types. The class method ``__get_validators__`` will be called
to get validators to parse and validate the input data.

.. note::

   The name of ``__get_validators__`` was changed from ``get_validators`` in ``v0.17``,
   the old name is currently still supported but deprecated and will be removed in future.

.. literalinclude:: examples/custom_data_types.py

(This script is complete, it should run "as is")

Helper Functions
................

*Pydantic* provides three ``classmethod`` helper functions on models for parsing data:

:parse_obj: this is almost identical to the ``__init__`` method of the model except if the object passed is not
  a dict ``ValidationError`` will be raised (rather than python raising a ``TypeError``).
:parse_raw: takes a *str* or *bytes* parses it as *json*, or *pickle* data and then passes
  the result to ``parse_obj``. The data type is inferred from the ``content_type`` argument,
  otherwise *json* is assumed.
:parse_file: reads a file and passes the contents to ``parse_raw``, if ``content_type`` is omitted it is inferred
  from the file's extension.

.. literalinclude:: examples/parse.py

(This script is complete, it should run "as is")

.. note::

   Since ``pickle`` allows complex objects to be encoded, to use it you need to explicitly pass ``allow_pickle`` to
   the parsing function.

.. _config:

Model Config
............

Behaviour of pydantic can be controlled via the ``Config`` class on a model.

Options:

:anystr_strip_whitespace: strip or not trailing and leading whitespace for str & byte types (default: ``False``)
:min_anystr_length: min length for str & byte types (default: ``0``)
:max_anystr_length: max length for str & byte types (default: ``2 ** 16``)
:validate_all: whether or not to validate field defaults (default: ``False``)
:extra: whether to ignore, allow or forbid extra attributes in model. Can use either string values of ``ignore``,
  ``allow`` or ``forbid``, or use ``Extra`` enum (default is ``Extra.ignore``)
:allow_mutation: whether or not models are faux-immutable, e.g. __setattr__ fails (default: ``True``)
:use_enum_values: whether to populate models with the ``value`` property of enums,
    rather than the raw enum - useful if you want to serialise ``model.dict()`` later (default: ``False``)
:fields: schema information on each field, this is equivilant to
    using :ref:`the schema <schema>` class (default: ``None``)
:validate_assignment: whether to perform validation on assignment to attributes or not (default: ``False``)
:allow_population_by_alias: whether or not an aliased field may be populated by its name as given by the model
    attribute, rather than strictly the alias; please be sure to read the warning below before enabling this (default:
    ``False``)
:error_msg_templates: let's you to override default error message templates.
    Pass in a dictionary with keys matching the error messages you want to override (default: ``{}``)
:arbitrary_types_allowed: whether to allow arbitrary user types for fields (they are validated simply by checking if the
    value is instance of that type). If False - RuntimeError will be raised on model declaration (default: ``False``)
:json_encoders: customise the way types are encoded to json, see :ref:`JSON Serialisation <json_dump>` for more
    details.

.. warning::

   Think twice before enabling ``allow_population_by_alias``! Enabling it could cause previously correct code to become
   subtly incorrect. As an example, say you have a field named ``card_number`` with the alias ``cardNumber``. With
   population by alias disabled (the default), trying to parse an object with only the key ``card_number`` will fail.
   However, if you enable population by alias, the ``card_number`` field can now be populated from ``cardNumber``
   **or** ``card_number``, and the previously-invalid example object would now be valid. This may be desired for some
   use cases, but in others (like the one given here, perhaps!), relaxing strictness with respect to aliases could
   introduce bugs.

.. literalinclude:: examples/config.py

(This script is complete, it should run "as is")

Version for models based on ``@dataclass`` decorator:

.. literalinclude:: examples/ex_dataclasses_config.py

(This script is complete, it should run "as is")

.. _settings:

Settings
........

One of pydantic's most useful applications is to define default settings, allow them to be overridden by
environment variables or keyword arguments (e.g. in unit tests).

.. literalinclude:: examples/settings.py

(This script is complete, it should run "as is")

Here ``redis_port`` could be modified via ``export MY_PREFIX_REDIS_PORT=6380`` or ``auth_key`` by
``export my_api_key=6380``.

By default ``BaseSettings`` considers field values in the following priority (where 3. has the highest priority
and overrides the other two):

1. The default values set in your ``Settings`` class
2. Environment variables eg. ``MY_PREFIX_REDIS_PORT`` as described above.
3. Argument passed to the ``Settings`` class on initialisation.

This behaviour can be changed by overriding the ``_build_values`` method on ``BaseSettings``.

Complex types like ``list``, ``set``, ``dict`` and submodels can be set by using JSON environment variables.

Environment variables can be read in a case insensitive manner:

.. literalinclude:: examples/settings_case_insensitive.py

Here ``redis_port`` could be modified via ``export APP_REDIS_HOST``, ``export app_redis_host``, ``export app_REDIS_host``, etc.

Dynamic model creation
......................

There are some occasions where the shape of a model is not known until runtime, for this *pydantic* provides
the ``create_model`` method to allow models to be created on the fly.

.. literalinclude:: examples/dynamic_model_creation.py

Here ``StaticFoobarModel`` and ``DynamicFoobarModel`` are identical.

Fields are defined by either a a tuple of the form ``(<type>, <default value>)`` or just a default value. The
special key word arguments ``__config__`` and ``__base__`` can be used to customise the new model. This includes
extending a base model with extra fields.

.. literalinclude:: examples/dynamic_inheritance.py

.. _usage_mypy:

Usage with mypy
...............

Pydantic works with `mypy <http://mypy-lang.org/>`_ provided you use the "annotation only" version of
required variables:

.. literalinclude:: examples/mypy.py

(This script is complete, it should run "as is")

You can also run it through mypy with::

    mypy --ignore-missing-imports --follow-imports=skip --strict-optional pydantic_mypy_test.py

Strict Optional
~~~~~~~~~~~~~~~

For your code to pass with ``--strict-optional`` you need to to use ``Optional[]`` or an alias of ``Optional[]``
for all fields with ``None`` default, this is standard with mypy.

Pydantic provides a few useful optional or union types:

* ``NoneStr`` aka. ``Optional[str]``
* ``NoneBytes`` aka. ``Optional[bytes]``
* ``StrBytes`` aka. ``Union[str, bytes]``
* ``NoneStrBytes`` aka. ``Optional[StrBytes]``

If these aren't sufficient you can of course define your own.

.. _usage_mypy_required:

Required Fields and mypy
~~~~~~~~~~~~~~~~~~~~~~~~

The ellipsis notation ``...`` will not work with mypy, you need to use annotation only fields as in the example above.

.. warning::

   Be aware that using annotation only fields will alter the order of your fields in metadata and errors:
   annotation only fields will always come first, but still in the order they were defined.

To get round this you can use the ``Required`` (via ``from pydantic import Required``) field as an alias for
ellipses or annotation only.

Faux Immutability
.................

Models can be configured to be immutable via ``allow_mutation = False`` this will prevent changing attributes of
a model.

.. warning::

   Immutability in python is never strict. If developers are determined/stupid they can always
   modify a so-called "immutable" object.

.. literalinclude:: examples/mutation.py

Trying to change ``a`` caused an error and it remains unchanged, however the dict ``b`` is mutable and the
immutability of ``foobar`` doesn't stop being changed.

Copying
.......

The ``dict`` function returns a dictionary containing the attributes of a model. Sub-models are recursively
converted to dicts, ``copy`` allows models to be duplicated, this is particularly useful for immutable models.


``dict``, ``copy``, and ``json`` (described :ref:`below <json_dump>`) all take the optional
``include`` and ``exclude`` keyword arguments to control which attributes are returned or copied,
respectively. ``copy`` accepts extra keyword arguments, ``update``, which accepts a ``dict`` mapping attributes
to new values that will be applied as the model is duplicated and ``deep`` to make a deep copy of the model.

``dict`` and ``json`` take the optional ``skip_defaults`` keyword argument which will skip attributes that were
not explicitly set. This is useful to reduce the serialized size of models thats have many default fields that
are not often changed.

.. literalinclude:: examples/copy_dict.py

Serialisation
.............

*pydantic* has native support for serialisation to **JSON** and **Pickle**, you can of course serialise to any
other format you like by processing the result of ``dict()``.

.. _json_dump:

JSON Serialisation
~~~~~~~~~~~~~~~~~~

The ``json()`` method will serialise a model to JSON, ``json()`` in turn calls ``dict()`` and serialises its result.

Serialisation can be customised on a model using the ``json_encoders`` config property, the keys should be types and
the values should be functions which serialise that type, see the example below.

If this is not sufficient, ``json()`` takes an optional ``encoder`` argument which allows complete control
over how non-standard types are encoded to JSON.

.. literalinclude:: examples/ex_json.py

(This script is complete, it should run "as is")

By default timedelta's are encoded as a simple float of total seconds. The ``timedelta_isoformat`` is provided
as an optional alternative which implements ISO 8601 time diff encoding.

Pickle Serialisation
~~~~~~~~~~~~~~~~~~~~

Using the same plumbing as ``copy()`` *pydantic* models support efficient pickling and unpicking.

.. literalinclude:: examples/ex_pickle.py

(This script is complete, it should run "as is")

Abstract Base Classes
.....................

Pydantic models can be used alongside Python's
`Abstract Base Classes <https://docs.python.org/3/library/abc.html>`_ (ABCs).

.. literalinclude:: examples/ex_abc.py

(This script is complete, it should run "as is")

.. _postponed_annotations:

Postponed Annotations
.....................

.. note::

   Both postponed annotations via the future import and ``ForwardRef`` require python 3.7+.

   Support for those features starts from *pydantic* v0.18.

Postponed annotations (as described in `PEP563 <https://www.python.org/dev/peps/pep-0563/>`_)
"just work".

.. literalinclude:: examples/postponed_annotations.py

(This script is complete, it should run "as is")

Internally *pydantic*  will call a method similar to ``typing.get_type_hints`` to resolve annotations.

In cases where the referenced type is not yet defined, ``ForwardRef`` can be used (although referencing the
type directly or by its string is a simpler solution in the case of
:ref:`self-referencing models <self_ref_models>`).

You may need to call ``Model.update_forward_refs()`` after creating the model,
this is because in the example below ``Foo`` doesn't exist before it has been created (obviously) so ``ForwardRef``
can't initially be resolved. You have to wait until after ``Foo`` is created, then call ``update_forward_refs``
to properly set types before the model can be used.

.. literalinclude:: examples/forward_ref.py

(This script is complete, it should run "as is")

.. warning::

   To resolve strings (type names) into annotations (types) *pydantic* needs a dict to lookup,
   for this is uses ``module.__dict__`` just as ``get_type_hints`` does. That means *pydantic* does not play well
   with types not defined in the global scope of a module.

   For example, this works fine:

   .. literalinclude:: examples/postponed_works.py

   While this will break:

   .. literalinclude:: examples/postponed_broken.py

   Resolving this is beyond the call for *pydantic*: either remove the future import or declare the types globally.

.. _benchmarks_tag:

Benchmarks
----------

Below are the results of crude benchmarks comparing *pydantic* to other validation libraries.

.. csv-table::
   :header: "Package", "Relative Performance", "Mean validation time", "std. dev."
   :align: center
   :file: benchmarks.csv

See `the benchmarks code <https://github.com/samuelcolvin/pydantic/tree/master/benchmarks>`_
for more details on the test case. Feel free to submit more benchmarks or improve an existing one.

Benchmarks were run with python 3.7.2 and the following package versions:

* **pydantic** pre ``v0.27``
  `d473f4a <https://github.com/samuelcolvin/pydantic/commit/d473f4abc9d040c8c90e102017aacfc078f0f37d>`_ compiled with
  cython
* **toasted-marshmallow** ``v0.2.6``
* **marshmallow** the version installed by ``toasted-marshmallow``, see
  `this <https://github.com/lyft/toasted-marshmallow/issues/9>`_ issue.
* **trafaret** ``v1.2.0``
* **django-restful-framework** ``v3.9.4``


Contributing to Pydantic
------------------------

We'd love you to contribute to *pydantic*, it should be extremely simple to get started and create a Pull Request.
*pydantic* is released regularly so you should see your improvements release in a matter of days or weeks.

If you're looking for something to get your teeth into, check out the
`"help wanted" <https://github.com/samuelcolvin/pydantic/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22>`_
label on github.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. Luckily since
*pydantic* has few dependencies, doesn't require compiling and tests don't need access to databases etc., setting
up and running tests should be very simple.

You'll need to have **python 3.6** or **3.7**, **virtualenv**, **git**, and **make** installed.

.. literalinclude:: examples/contributing.sh
  :language: bash

**tl;dr**: use ``make format`` to fix formatting, ``make`` to run tests and linting & ``make docs``
to build docs.

Using Pydantic
--------------

Third party libraries based on *pydantic*.

* `FastAPI <https://github.com/tiangolo/fastapi>`_ is a high performance API framework, easy to learn,
  fast to code and ready for production, based on *pydantic* and Starlette.
* `aiohttp-toolbox <https://github.com/samuelcolvin/aiohttp-toolbox>`_ numerous utilities for aiohttp including
  data parsing using *pydantic*.
* `harrier <https://github.com/samuelcolvin/harrier>`_ a better static site generator built with python.

More packages using pydantic can be found by visiting
`pydantic's page on libraries.io <https://libraries.io/pypi/pydantic>`_.


.. include:: .TMP_HISTORY.rst


.. |pypi| image:: https://img.shields.io/pypi/v/pydantic.svg
   :target: https://pypi.python.org/pypi/pydantic
.. |license| image:: https://img.shields.io/pypi/l/pydantic.svg
   :target: https://github.com/samuelcolvin/pydantic
