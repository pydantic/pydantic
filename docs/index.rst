pydantic
========

.. toctree::
   :maxdepth: 2

|pypi| |license|

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

* ``id`` is of type int; the annotation only declaration tells pydantic that this field is required. Strings,
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

So *pydantic* uses some cool new language feature, but why should I actually go an use it?

**no brainfuck**
    no new schema definition micro-language to learn. If you know python (and perhaps skim read the
    `type hinting docs <https://docs.python.org/3/library/typing.html>`_) you know how to use pydantic.

**plays nicely with your IDE/linter/brain**
    because pydantic data structures are just instances of classes you define; auto-completion, linting,
    :ref:`mypy <usage_mypy>` and your intuition should all work properly with your validated data.

**dual use**
    pydantic's :ref:`BaseSettings <settings>` class allows it to be used in both a "validate this request data" context
    and "load my system settings" context. The main difference being that system settings can have defaults changed
    by environment variables and more complex objects like DSNs and python objects are often required.

**fast**
    In :ref:`benchmarks <benchmarks_tag>` pydantic is faster than all other tested libraries.

**validate complex structures**
    use of recursive pydantic models, ``typing``'s ``List`` and ``Dict`` etc. and validators allow
    complex data schemas to be clearly and easily defined can then checked.

**extendible**
    pydantic allows custom data types to be defined or you can extend validation with methods on a model decorated
    with the ``validator`` decorator.


Install
-------

Just::

    pip install pydantic

pydantic has no required dependencies except python 3.6+. If you've got python 3.6 and ``pip`` installed -
you're good to go.

If you want *pydantic* to parse msgpack you can add `msgpack-python <https://pypi.python.org/pypi/msgpack-python>`_
as an optional dependency, same goes for reading json faster with `ujson <https://pypi.python.org/pypi/ujson>`_::

    pip install pydantic[msgpack]
    # or
    pip install pydantic[ujson]
    # or just
    pip install pydantic[msgpack,ujson]

Usage
-----

PEP 484 Types
.............

pydantic uses ``typing`` types to define more complex objects.

.. literalinclude:: examples/ex_typing.py

(This script is complete, it should run "as is")

Choices
.......

pydantic uses python's standard ``enum`` classes to define choices.

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

Validators can do a few more complex things:

.. literalinclude:: examples/validators_complex.py

(This script is complete, it should run "as is")

A few more things to note:

* a single validator can apply to multiple fields
* the keyword argument ``pre`` will cause validators to be called prior to other validation
* the ``whole`` keyword argument will mean validators are applied to entire objects rather than individual values
  (applies for complex typing objects eg. ``List``, ``Dict``, ``Set``)


Recursive Models
................

More complex hierarchical data structures can be defined using models as types in annotations themselves.

The ellipsis ``...`` just means "Required" same as annotation only declarations above.

.. literalinclude:: examples/recursive.py

(This script is complete, it should run "as is")

Error Handling
..............

.. literalinclude:: examples/errors.py

(This script is complete, it should run "as is")

Exotic Types
............

pydantic comes with a number of utilities for parsing or validating common objects.

.. literalinclude:: examples/exotic.py

(This script is complete, it should run "as is")

Helper Functions
................

*Pydantic* provides three ``classmethod`` helper functions on models for parsing data:

:parse_obj: this is almost identical to the ``__init__`` method of the model except if the object passed is not
  a dict ``ValidationError`` will be raised (rather than python raising a ``TypeError``).
:parse_raw: takes a *str* or *bytes* parses it as *json*, *msgpack* or *pickle* data and then passes
  the result to ``parse_obj``. The data type is inferred from the ``content_type`` argument,
  otherwise *json* is assumed.
:parse_file: reads a file and passes the contents to ``parse_raw``, if ``content_type`` is omitted it is inferred
  from the file's extension.

.. literalinclude:: examples/parse.py

(This script is complete, it should run "as is" provided ``msgpack-python`` is installed)

.. note::

   Since ``pickle`` allows complex objects to be encoded, to use it you need to explicitly pass ``allow_pickle`` to
   the parsing function.

Model Config
............

Behaviour of pydantic can be controlled via the ``Config`` class on a model.

Options:

:min_anystr_length: min length for str & byte types (default: ``0``)
:max_anystr_length: max length for str & byte types (default: ``2 ** 16``)
:min_number_size: min size for numbers (default: ``-2 ** 64``)
:max_number_size: max size for numbers (default: ``2 ** 64``)
:validate_all: whether or not to validate field defaults (default: ``False``)
:ignore_extra: whether to ignore any extra values in input data (default: ``True``)
:allow_extra: whether or not too allow (and include on the model) any extra values in input data (default: ``False``)
:allow_mutation: whether or not models are faux-immutable, e.g. __setattr__ fails (default: ``True``)
:fields: extra information on each field, currently just "alias" is allowed (default: ``None``)
:validate_assignment: whether to perform validation on assignment to attributes or not (default: ``False``)

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

Copy and Values
...............

The ``values`` function returns a dict containing the attributes of a model sub-model are recursively
converted to dicts.

While ``copy`` allows models to be duplicated, this is particularly useful for immutable models.

Both ``values`` and ``copy`` take the optional ``include`` and ``exclude`` keyword arguments to control which attributes
are return/copied. ``copy`` allows an extra keyword argument ``update`` allowing attributes to be modified as the model
is duplicated.

.. literalinclude:: examples/copy_values.py

Pickle
......

Using the same plumbing as ``copy()`` pydantic models support efficient pickling and unpicking.

.. literalinclude:: examples/ex_pickle.py

.. _benchmarks_tag:

Benchmarks
----------

Below are the results of crude benchmarks comparing *pydantic* to other validation libraries.

.. csv-table::
   :header: "Package", "Mean deserialization time", "std. dev."
   :align: center
   :file: benchmarks.csv

(See `the benchmarks code <https://github.com/samuelcolvin/pydantic/tree/master/benchmarks>`_
for more details on the test case. Feel free to submit more benchmarks or improve an existing one.)

.. include:: ../HISTORY.rst


.. |pypi| image:: https://img.shields.io/pypi/v/pydantic.svg
   :target: https://pypi.python.org/pypi/pydantic
.. |license| image:: https://img.shields.io/pypi/l/pydantic.svg
   :target: https://github.com/samuelcolvin/pydantic
