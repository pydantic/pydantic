import warnings
from contextlib import contextmanager
from typing import Annotated, Literal

import pytest
from typing_extensions import Self, deprecated

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


@contextmanager
def error_on_deprecationwarning():
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        yield


@pytest.fixture(params=(None, 'get', 'set', 'get_and_set'))
def mode(request: pytest.FixtureRequest) -> Literal[None, 'get', 'set', 'get_and_set']:
    return request.param


@pytest.fixture
def config(mode) -> ConfigDict:
    config = ConfigDict()
    if mode is not None:
        config['warn_deprecated'] = mode
    return config


def test_deprecated_fields(mode, config):
    class Model(BaseModel):
        model_config = config
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

    with pytest.warns(DeprecationWarning, match='^$') if mode != 'set' else error_on_deprecationwarning():
        instance.a

    with (
        pytest.warns(DeprecationWarning, match='^$')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        instance.a = 2

    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode != 'set'
        else error_on_deprecationwarning()
    ):
        b = instance.b

    assert b == 1

    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        instance.b = 2


def test_deprecated_fields_deprecated_class(mode, config):
    class Model(BaseModel):
        model_config = config
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

    with pytest.warns(DeprecationWarning, match='^$') if mode != 'set' else error_on_deprecationwarning():
        instance.a
    with (
        pytest.warns(DeprecationWarning, match='^$')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        instance.a = 2
    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode != 'set'
        else error_on_deprecationwarning()
    ):
        instance.b
    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        instance.b = 2
    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode != 'set'
        else error_on_deprecationwarning()
    ):
        instance.c
    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        instance.c = 2


def test_deprecated_fields_field_validator(mode, config):
    class Model(BaseModel):
        model_config = config
        x: int = Field(deprecated='x is deprecated')

        @field_validator('x')
        @classmethod
        def validate_x(cls, v: int) -> int:
            return v * 2

    instance = Model(x=1)

    with pytest.warns(DeprecationWarning) if mode != 'set' else error_on_deprecationwarning():
        assert instance.x == 2
    with pytest.warns(DeprecationWarning) if mode in ('set', 'get_and_set') else error_on_deprecationwarning():
        instance.x = 3


def test_deprecated_fields_model_validator(mode, config):
    class Model(BaseModel):
        model_config = config
        x: int = Field(deprecated='x is deprecated')

        @model_validator(mode='after')
        def validate_x(self) -> Self:
            self.x = self.x * 2
            return self

    with pytest.warns(DeprecationWarning):
        instance = Model(x=1)
    with pytest.warns(DeprecationWarning) if mode != 'set' else error_on_deprecationwarning():
        assert instance.x == 2
    with pytest.warns(DeprecationWarning) if mode in ('set', 'get_and_set') else error_on_deprecationwarning():
        instance.x = 3


def test_deprecated_fields_validate_assignment(mode, config):
    class Model(BaseModel):
        x: int = Field(deprecated='x is deprecated')

        model_config = config | {'validate_assignment': True}

    instance = Model(x=1)

    with pytest.warns(DeprecationWarning) if mode != 'set' else error_on_deprecationwarning():
        assert instance.x == 1

    with pytest.warns(DeprecationWarning) if mode in ('set', 'get_and_set') else error_on_deprecationwarning():
        instance.x = 2

    with pytest.warns(DeprecationWarning) if mode != 'set' else error_on_deprecationwarning():
        assert instance.x == 2


def test_computed_field_deprecated(mode, config):
    class Model(BaseModel):
        model_config = config

        @computed_field
        @property
        @deprecated('This is deprecated')
        def p1(self) -> int:
            return 1

        @computed_field(deprecated='This is deprecated')
        @property
        @deprecated('This is deprecated (this message is the one emitted)')
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

    with pytest.warns(DeprecationWarning, match='^This is deprecated$'):
        instance.p1
    # Ideally, the deprecation message from `@computed_field` should take priority,
    # but we can't safely unwrap the decorated property from `@deprecated` (see note in
    # `set_deprecated_descriptors()`):
    with pytest.warns(DeprecationWarning, match=r'^This is deprecated \(this message is the one emitted\)$'):
        instance.p2
    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode != 'set'
        else error_on_deprecationwarning()
    ):
        instance.p4
    with pytest.warns(DeprecationWarning, match='^This is deprecated$'):
        instance.p5

    with pytest.warns(DeprecationWarning, match='^$') if mode != 'set' else error_on_deprecationwarning():
        p3 = instance.p3

    assert p3 == 1


def test_computed_field_deprecated_deprecated_class(mode, config):
    class Model(BaseModel):
        model_config = config

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

    with (
        pytest.warns(DeprecationWarning, match='^This is deprecated$')
        if mode != 'set'
        else error_on_deprecationwarning()
    ):
        p1 = instance.p1

    with pytest.warns(DeprecationWarning, match='^deprecated$') if mode != 'set' else error_on_deprecationwarning():
        p2 = instance.p2

    with (
        pytest.warns(DeprecationWarning, match='^This is a deprecated string$')
        if mode != 'set'
        else error_on_deprecationwarning()
    ):
        p3 = instance.p3

    assert p1 == 1
    assert p2 == 2
    assert p3 == 3


def test_deprecated_with_boolean(mode, config) -> None:
    class Model(BaseModel):
        model_config = config

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

    with pytest.warns(DeprecationWarning, match='deprecated') if mode != 'set' else error_on_deprecationwarning():
        instance.a
    with (
        pytest.warns(DeprecationWarning, match='deprecated')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        instance.a = 2


def test_computed_field_deprecated_class_access() -> None:
    class Model(BaseModel):
        @computed_field(deprecated=True)
        def prop(self) -> int:
            return 1

    assert isinstance(Model.prop, property)


def test_computed_field_deprecated_subclass() -> None:
    """https://github.com/pydantic/pydantic/issues/10384"""

    class Base(BaseModel):
        @computed_field(deprecated=True)
        def prop(self) -> int:
            return 1

    class Sub(Base):
        pass


def test_deprecated_field_forward_annotation(mode, config) -> None:
    """https://github.com/pydantic/pydantic/issues/11390"""

    class Model(BaseModel):
        model_config = config

        a: "Annotated[Test, deprecated('test')]" = 2

    Test = int

    Model.model_rebuild()
    assert isinstance(Model.model_fields['a'].deprecated, deprecated)
    assert Model.model_fields['a'].deprecated.message == 'test'

    m = Model()

    with pytest.warns(DeprecationWarning, match='test') if mode != 'set' else error_on_deprecationwarning():
        m.a
    with (
        pytest.warns(DeprecationWarning, match='test')
        if mode in ('set', 'get_and_set')
        else error_on_deprecationwarning()
    ):
        m.a = 1


def test_deprecated_field_with_assignment() -> None:
    class Model(BaseModel):
        # A buggy implementation made it so that deprecated wouldn't
        # appear on the `FieldInfo`:
        a: Annotated[int, deprecated('test')] = Field(default=1)

    assert isinstance(Model.model_fields['a'].deprecated, deprecated)
    assert Model.model_fields['a'].deprecated.message == 'test'
