pydantic
========

|BuildStatus| |Coverage| |pypi| |CondaForge| |downloads| |versions| |license|

Data validation and settings management using Python type hinting.

Fast and extensible, *pydantic* plays nicely with your linters/IDE/brain.
Define how data should be in pure, canonical Python 3.6+; validate it with *pydantic*.


Help
----

See `documentation`_ for more details.


Installation
------------

Install using ``pip install -U pydantic`` or ``conda install pydantic -c conda-forge``.
For more installation options to make *pydantic* even faster, see `Install`_ section in the documentation.


A Simple Example
----------------

.. code-block:: python

    from datetime import datetime
    from typing import List
    from pydantic import BaseModel

    class User(BaseModel):
        id: int
        name = 'John Doe'
        signup_ts: datetime = None
        friends: List[int] = []

    external_data = {'id': '123', 'signup_ts': '2017-06-01 12:22', 'friends': [1, '2', b'3']}
    user = User(**external_data)
    print(user)
    # > User id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]
    print(user.id)
    # > 123


Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to *pydantic*, see the `Contributing to Pydantic`_.


.. |BuildStatus| image:: https://travis-ci.org/samuelcolvin/pydantic.svg?branch=master
   :target: https://travis-ci.org/samuelcolvin/pydantic
.. |Coverage| image:: https://codecov.io/gh/samuelcolvin/pydantic/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/samuelcolvin/pydantic
.. |pypi| image:: https://img.shields.io/pypi/v/pydantic.svg
   :target: https://pypi.python.org/pypi/pydantic
.. |CondaForge| image:: https://img.shields.io/conda/v/conda-forge/pydantic.svg
   :target: https://anaconda.org/conda-forge/pydantic
.. |downloads| image:: https://img.shields.io/pypi/dm/pydantic.svg
   :target: https://pypistats.org/packages/pydantic
.. |versions| image:: https://img.shields.io/pypi/pyversions/pydantic.svg
   :target: https://github.com/samuelcolvin/pydantic
.. |license| image:: https://img.shields.io/github/license/samuelcolvin/pydantic.svg
   :target: https://github.com/samuelcolvin/pydantic/blob/master/LICENSE
.. _documentation: https://pydantic-docs.helpmanual.io/
.. _Install: https://pydantic-docs.helpmanual.io/#install
.. _Contributing to Pydantic: https://pydantic-docs.helpmanual.io/#contributing-to-pydantic
