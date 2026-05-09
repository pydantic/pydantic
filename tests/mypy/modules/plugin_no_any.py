"""Regression test for https://github.com/pydantic/pydantic/issues/13161.

Even when ``init_forbid_extra`` is enabled, a dynamic validation alias forces the
plugin to add ``**kwargs`` to ``__init__`` because the static signature can't be
fully determined. The synthesized ``Any`` for ``**kwargs`` should not trip
``--disallow-any-explicit``.
"""

from pydantic import AliasChoices, AliasPath, BaseModel, Field


class ModelWithAliasChoices(BaseModel):
    test_field: str = Field(default='', validation_alias=AliasChoices('choice', 'other_choice'))


class ModelWithAliasPath(BaseModel):
    test_field: str = Field(default='', validation_alias=AliasPath('outer', 'inner'))


class ModelWithAliasGenerator(BaseModel):
    model_config = {'alias_generator': str.upper}

    test_field: str = ''
