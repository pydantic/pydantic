pydantic
========

.. toctree::
   :maxdepth: 2

|pypi| |license| |gitter|

Current Version: |version|

Data validation and settings management using python 3.6 type hinting.

Define how data should be in pure, canonical python; validate it with *pydantic*.

`PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_ introduced type hinting into python 3.5,
`PEP 526 <https://www.python.org/dev/peps/pep-0526/>`_ extended that with syntax for variable annotation in python 3.6.

*pydantic* uses those annotations to validate that untrusted data takes the form you want.

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
    *pydantic's* :ref:`BaseSettings <settings>` class allows it to be used in both a "validate this request data" context
    and "load my system settings" context. The main difference being that system settings can have defaults changed
    by environment variables and more complex objects like DSNs and python objects are often required.

**fast**
    In :ref:`benchmarks <benchmarks_tag>` *pydantic* is faster than all other tested libraries.

**validate complex structures**
    use of recursive *pydantic* models, ``typing``'s ``List`` and ``Dict`` etc. and validators allow
    complex data schemas to be clearly and easily defined and then checked.

**extendible**
    *pydantic* allows custom data types to be defined or you can extend validation with methods on a model decorated
    with the ``validator`` decorator.


Install
-------

Just::

    pip install pydantic

*pydantic* has no required dependencies except python 3.6+. If you've got python 3.6 and ``pip`` installed -
you're good to go.

If you want *pydantic* to parse json faster you can add `ujson <https://pypi.python.org/pypi/ujson>`_
as an optional dependency. Similarly if *pydantic's* email validation relies on
`email-validator <https://github.com/JoshData/python-email-validator>`_ ::

    pip install pydantic[ujson]
    # or
    pip install pydantic[email]
    # or just
    pip install pydantic[ujson,email]

Of course you can also install these requirements manually with ``pip install ...``.

Usage
-----

PEP 484 Types
.............

*pydantic* uses ``typing`` types to define more complex objects.

.. literalinclude:: examples/ex_typing.py

(This script is complete, it should run "as is")

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
* their signature can with be ``(cls, value)`` or ``(cls, value, *, values, config, field)``
* validator should either return the new value or raise a ``ValueError`` or ``TypeError``
* where validators rely on other values, you should be aware that:

  - Validation is done in the order fields are defined, eg. here ``password2`` has access to ``password1``
    (and ``name``), but ``password1`` does not have access to ``password2``. You should heed the warning
    :ref:`below <usage_mypy_required>` regarding field order and required fields.

  - If validation fails on another field (or that field is missing) it will not be included in ``values``, hence
    ``if 'password1' in values and ...`` in this example.

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


Field Checks
~~~~~~~~~~~~

.. note::

   New in version ``v0.8.0``.

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

.. _schema:

Schema Creation
...............

*Pydantic* allows auto creation of schemas from models:

.. literalinclude:: examples/schema1.py

Outputs:

.. literalinclude:: examples/schema1.json

(This script is complete, it should run "as is")

`schema` will return a dict of the schema, while `schema_json` will return a JSON representation of that.

"submodels" are recursively included in the schema.

The ``description`` for models is taken from the docstring of the class.

Enums are shown in the schema as choices, optionally the ``choice_names`` argument can be used
to provide human friendly descriptions for the choices. If  ``choice_names`` is omitted or misses values,
descriptions will be generated by calling ``.title()`` on the name of the member.

Optionally the ``Schema`` class can be used to provide extra information about the field, arguments:

* ``default`` (positional argument), since the ``Schema`` is replacing the field's default, its first
  argument is used to set the default, use ellipsis (``...``) to indicate the field is required
* ``title`` if omitted ``field_name.title()`` is used
* ``choice_names`` as described above
* ``alias`` - the public name of the field.
* ``**`` any other keyword arguments (eg. ``description``) will be added verbatim to the field's schema

Instead of using ``Schema``, the ``fields`` property of :ref:`the Config class <config>` can be used
to set all the arguments above except ``default``.

The schema is generated by default using aliases as keys, it can also be generated using model
property names not aliases with ``MainModel.schema/schema_json(by_alias=False)``.

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

Exotic Types
............

*Pydantic* comes with a number of utilities for parsing or validating common objects.

.. literalinclude:: examples/exotic.py

(This script is complete, it should run "as is")

Json Type
.........

You can use ``Json`` data type - *Pydantic* will first parse raw JSON string and then will validate parsed object
against defined Json structure if it's provided.

.. literalinclude:: examples/ex_json_type.py

(This script is complete, it should run "as is")

Custom Data Types
.................

You can also define your own data types. Class method ``get_validators`` will be called to get validators to parse and
validate the input data.

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
:ignore_extra: whether to ignore any extra values in input data (default: ``True``)
:allow_extra: whether or not too allow (and include on the model) any extra values in input data (default: ``False``)
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

.. _settings:

Settings
........

One of pydantic's most useful applications is to define default settings, allow them to be overridden by
environment variables or keyword arguments (e.g. in unit tests).

This usage example comes last as it uses numerous concepts described above.

.. literalinclude:: examples/settings.py

(This script is complete, it should run "as is")

Here ``redis_port`` could be modified via ``export MY_PREFIX_REDIS_PORT=6380`` or ``auth_key`` by
``export my_api_key=6380``.

Complex types like ``list``, ``set``, ``dict`` and submodels can be set by using JSON environment variables.

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

This script is complete, it should run "as is". You can also run it through mypy with::

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
respectively. ``copy`` accepts an extra keyword argument, ``update``, which accepts a ``dict`` mapping attributes
to new values that will be applied as the model is duplicated.

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

.. _benchmarks_tag:

Benchmarks
----------

Below are the results of crude benchmarks comparing *pydantic* to other validation libraries.

.. csv-table::
   :header: "Package", "Relative Performance", "Mean validation time", "std. dev."
   :align: center
   :file: benchmarks.csv

(See `the benchmarks code <https://github.com/samuelcolvin/pydantic/tree/master/benchmarks>`_
for more details on the test case. Feel free to submit more benchmarks or improve an existing one.)

.. include:: .TMP_HISTORY.rst


.. |pypi| image:: https://img.shields.io/pypi/v/pydantic.svg
   :target: https://pypi.python.org/pypi/pydantic
.. |license| image:: https://img.shields.io/pypi/l/pydantic.svg
   :target: https://github.com/samuelcolvin/pydantic
.. |gitter| image:: https://badges.gitter.im/pydantic.svg
   :target: https://gitter.im/pydantic/Lobby
