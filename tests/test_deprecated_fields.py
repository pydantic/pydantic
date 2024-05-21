import importlib.metadata

import pytest
from packaging.version import Version
from typing_extensions import Annotated, Self, deprecated

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


def test_deprecated_fields():
    class Model(BaseModel):
        a: Annotated[int, Field(deprecated='')]
        b: Annotated[int, Field(deprecated='This is deprecated')]
        c: Annotated[int, Field(deprecated=None)]

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'deprecated': True, 'title': 'A', 'type': 'integer'},
            'b': {'deprecated': True, 'title': 'B', 'type': 'integer'},
            'c': {'title': 'C', 'type': 'integer'},
        },
        'required': ['a', 'b', 'c'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model(a=1, b=1, c=1)

    pytest.warns(DeprecationWarning, lambda: instance.a, match='^$')

    with pytest.warns(DeprecationWarning, match='^This is deprecated$'):
        b = instance.b

    assert b == 1


@pytest.mark.skipif(
    Version(importlib.metadata.version('typing_extensions')) < Version('4.9'),
    reason='`deprecated` type annotation requires typing_extensions>=4.9',
)
def test_deprecated_fields_deprecated_class():
    class Model(BaseModel):
        a: Annotated[int, deprecated('')]
        b: Annotated[int, deprecated('This is deprecated')] = 1
        c: Annotated[int, Field(deprecated=deprecated('This is deprecated'))] = 1

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'deprecated': True, 'title': 'A', 'type': 'integer'},
            'b': {'default': 1, 'deprecated': True, 'title': 'B', 'type': 'integer'},
            'c': {'default': 1, 'deprecated': True, 'title': 'C', 'type': 'integer'},
        },
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model(a=1)

    pytest.warns(DeprecationWarning, lambda: instance.a, match='^$')
    pytest.warns(DeprecationWarning, lambda: instance.b, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.c, match='^This is deprecated$')


def test_deprecated_fields_field_validator():
    class Model(BaseModel):
        x: int = Field(deprecated='x is deprecated')

        @field_validator('x')
        @classmethod
        def validate_x(cls, v: int) -> int:
            return v * 2

    instance = Model(x=1)

    with pytest.warns(DeprecationWarning):
        assert instance.x == 2


def test_deprecated_fields_model_validator():
    class Model(BaseModel):
        x: int = Field(deprecated='x is deprecated')

        @model_validator(mode='after')
        def validate_x(self) -> Self:
            self.x = self.x * 2
            return self

    with pytest.warns(DeprecationWarning):
        instance = Model(x=1)
        assert instance.x == 2


def test_deprecated_fields_validate_assignment():
    class Model(BaseModel):
        x: int = Field(deprecated='x is deprecated')

        model_config = {'validate_assignment': True}

    instance = Model(x=1)

    with pytest.warns(DeprecationWarning):
        assert instance.x == 1

    instance.x = 2

    with pytest.warns(DeprecationWarning):
        assert instance.x == 2


def test_computed_field_deprecated():
    class Model(BaseModel):
        @computed_field
        @property
        @deprecated('This is deprecated')
        def p1(self) -> int:
            return 1

        @computed_field(deprecated='This is deprecated')
        @property
        @deprecated('This is deprecated (this message is overridden)')
        def p2(self) -> int:
            return 1

        @computed_field(deprecated='')
        @property
        def p3(self) -> int:
            return 1

        @computed_field(deprecated='This is deprecated')
        @property
        def p4(self) -> int:
            return 1

        @computed_field
        @deprecated('This is deprecated')
        def p5(self) -> int:
            return 1

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'p1': {'deprecated': True, 'readOnly': True, 'title': 'P1', 'type': 'integer'},
            'p2': {'deprecated': True, 'readOnly': True, 'title': 'P2', 'type': 'integer'},
            'p3': {'deprecated': True, 'readOnly': True, 'title': 'P3', 'type': 'integer'},
            'p4': {'deprecated': True, 'readOnly': True, 'title': 'P4', 'type': 'integer'},
            'p5': {'deprecated': True, 'readOnly': True, 'title': 'P5', 'type': 'integer'},
        },
        'required': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model()

    pytest.warns(DeprecationWarning, lambda: instance.p1, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p2, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p4, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p5, match='^This is deprecated$')

    with pytest.warns(DeprecationWarning, match='^$'):
        p3 = instance.p3

    assert p3 == 1


@pytest.mark.skipif(
    Version(importlib.metadata.version('typing_extensions')) < Version('4.9'),
    reason='`deprecated` type annotation requires typing_extensions>=4.9',
)
def test_computed_field_deprecated_deprecated_class():
    class Model(BaseModel):
        @computed_field(deprecated=deprecated('This is deprecated'))
        @property
        def p1(self) -> int:
            return 1

        @computed_field(deprecated=True)
        @property
        def p2(self) -> int:
            return 2

        @computed_field(deprecated='This is a deprecated string')
        @property
        def p3(self) -> int:
            return 3

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'p1': {'deprecated': True, 'readOnly': True, 'title': 'P1', 'type': 'integer'},
            'p2': {'deprecated': True, 'readOnly': True, 'title': 'P2', 'type': 'integer'},
            'p3': {'deprecated': True, 'readOnly': True, 'title': 'P3', 'type': 'integer'},
        },
        'required': ['p1', 'p2', 'p3'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model()

    with pytest.warns(DeprecationWarning, match='^This is deprecated$'):
        p1 = instance.p1

    with pytest.warns(DeprecationWarning, match='^deprecated$'):
        p2 = instance.p2

    with pytest.warns(DeprecationWarning, match='^This is a deprecated string$'):
        p3 = instance.p3

    assert p1 == 1
    assert p2 == 2
    assert p3 == 3


def test_deprecated_with_boolean() -> None:
    class Model(BaseModel):
        a: Annotated[int, Field(deprecated=True)]
        b: Annotated[int, Field(deprecated=False)]

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'deprecated': True, 'title': 'A', 'type': 'integer'},
            'b': {'title': 'B', 'type': 'integer'},
        },
        'required': ['a', 'b'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model(a=1, b=1)

    pytest.warns(DeprecationWarning, lambda: instance.a, match='deprecated')
