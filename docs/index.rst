pydantic
========

.. toctree::
   :maxdepth: 2

|pypi| |license|

Current Version: |version|

Data validation and settings management using python 3.6 type hinting.

Define how data should be in pure canonical python, validate it with *pydantic*.

`PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_ introduced typing hinting into python in 3.5 and
`PEP 526 <https://www.python.org/dev/peps/pep-0526/>`_ extended that with syntax for variable annotation in 3.6.
*pydantic* uses those annotations to validate that untrusted data takes the form you want.

Simple example:

.. literalinclude:: example1.py

(This script is complete, it should run "as is")

What's going on here:

* ``id`` is of type int, the elipisis tells pydantic this field is required. Strings, bytes or floats will be
  converted to ints if possible, otherwise an exception would be raised.
* ``name`` pydantic infers is a string from the default, it is not required as it has a default
* ``signup_ts`` is a datetime field which is not required (``None`` if it's not supplied), pydantic will process
  either a unix timestamp int (eg. ``1496498400``) or a string representing the date & time.

If validation fails pydantic with raise an error with a breakdown of what was wrong:

.. literalinclude:: example2.py

Rationale
---------

So *pydantic* uses some cool new language feature, but why should I actually go an use it?

**no brainfuck**
    no new schema definition micro-language to learn. If you know python (and perhaps skim read the
    `type hinting docs <https://docs.python.org/3/library/typing.html>`_) you know how to use pydantic.

**plays nicely with your IDE/linter/brain**
    because pydantic data structures are just instances of classes you define; autocompleting, linting,
    `mypy <http://mypy-lang.org/>`_ your intuition should all work properly with your validated data.

**dual use**
    pydantic's :ref:`BaseSettings <settings>` class allows it to be used in both a "validate this request data" context
    and "load my system settings" context. The main difference being that system settings can can have defaults changed
    by environment variables and are otherwise only changed in unit tests.

**fast**
    In `benchmarks <https://github.com/samuelcolvin/pydantic/tree/master/benchmarks>`_ pydantic is around twice as
    fast as `trafaret <https://github.com/tailhook/trafaret>`_. Other comparisons to cerberus, DRF, jsonmodels to come.

**validate complex structures**
    use of recursive pydantic models and ``typing``'s ``List`` and ``Dict`` etc. allow complex data schemas to be
    clearly and easily defined.

**extendible**
    pydantic allows custom data types to be defined or you can extend validation with the `clean_*` methods on a model.


Install
-------

Just::

    pip install pydantic

pydantic has no dependencies except python 3.6+. If you've got python 3.6 and ``pip`` installed - you're good to go.

Usage
-----

Compound Types
..............

pyandtic uses ``typing`` types to define more complex objects.

.. literalinclude:: usage_compound.py

(This script is complete, it should run "as is")

Choices
.......

pyandtic uses python's standard ``enum`` classes to define value chocies.

.. literalinclude:: usage_choices.py

(This script is complete, it should run "as is")

Recursive Models
................

More complex hierarchical data structures can be defined using models as types in annotations themselves.

.. literalinclude:: usage_recursive.py

(This script is complete, it should run "as is")

Error Handling
..............

.. literalinclude:: usage_errors.py

(This script is complete, it should run "as is")

Exotic Types
............

pydantic comes with a number of utilities for parsing or validating common objects.

.. literalinclude:: usage_exotic.py

(This script is complete, it should run "as is")


Model Config
............

Behaviour of pydantic can be controlled via the ``Config`` class on a model.

Here default for config parameter are shown together with their meaning.

.. literalinclude:: usage_config.py

.. _settings:

Settings
........

One of pydantics most useful applications is to define default settings, allow them to be overridden by
environment variables are keyword arguments (eg. in unit tests).

This usage example comes last as it uses numerous concepts described above.

.. literalinclude:: usage_settings.py

Here ``redis_port`` could be modified via ``export MY_PREFIX_REDIS_PORT=6380`` or ``auth_key`` by
``export my_api_key=6380``.

.. include:: ../HISTORY.rst

.. |pypi| image:: https://img.shields.io/pypi/v/pydantic.svg
   :target: https://pypi.python.org/pypi/pydantic
.. |license| image:: https://img.shields.io/pypi/l/pydantic.svg
   :target: https://github.com/samuelcolvin/pydantic
