import importlib.metadata

import pytest
from typing_extensions import Annotated, deprecated

import pydantic
from pydantic import BaseModel, Field, computed_field


def test_deprecated_fields_field_function():
    class Model(BaseModel):
        a: Annotated[int, Field(deprecated='')]
        b: Annotated[int, Field(deprecated='This is deprecated')]
        c: Annotated[int, Field(deprecated=None)]
        d: Annotated[int, Field(deprecated=deprecated('This is deprecated'))]

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'deprecated': True, 'title': 'A', 'type': 'integer'},
            'b': {'deprecated': True, 'title': 'B', 'type': 'integer'},
            'c': {'title': 'C', 'type': 'integer'},
            'd': {'deprecated': True, 'title': 'D', 'type': 'integer'},
        },
        'required': ['a', 'b', 'c', 'd'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model(a=1, b=1, c=1)

    pytest.warns(DeprecationWarning, lambda: instance.a, match='^$')
    pytest.warns(DeprecationWarning, lambda: instance.b, match='^This is deprecated$')


@pytest.mark.skipif(
    pydantic.version.parse_package_version(importlib.metadata.version('typing_extensions')) < (4, 9),
    reason='`deprecated` type annotation requires typing_extensions>=4.9',
)
def test_deprecated_fields():
    class Model(BaseModel):
        a: Annotated[int, deprecated('')]
        b: Annotated[int, deprecated('This is deprecated')] = 1

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'deprecated': True, 'title': 'A', 'type': 'integer'},
            'b': {'default': 1, 'deprecated': True, 'title': 'B', 'type': 'integer'},
        },
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model(a=1)

    pytest.warns(DeprecationWarning, lambda: instance.a, match='^$')
    pytest.warns(DeprecationWarning, lambda: instance.b, match='^This is deprecated$')


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

        @computed_field(deprecated=deprecated('This is deprecated'))
        @property
        def p5(self) -> int:
            return 1

        @computed_field
        @deprecated('This is deprecated')
        def p6(self) -> int:
            return 1

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'p1': {'deprecated': True, 'readOnly': True, 'title': 'P1', 'type': 'integer'},
            'p2': {'deprecated': True, 'readOnly': True, 'title': 'P2', 'type': 'integer'},
            'p3': {'deprecated': True, 'readOnly': True, 'title': 'P3', 'type': 'integer'},
            'p4': {'deprecated': True, 'readOnly': True, 'title': 'P4', 'type': 'integer'},
            'p5': {'deprecated': True, 'readOnly': True, 'title': 'P4', 'type': 'integer'},
            'p6': {'deprecated': True, 'readOnly': True, 'title': 'P6', 'type': 'integer'},
        },
        'required': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
        'title': 'Model',
        'type': 'object',
    }

    instance = Model()

    pytest.warns(DeprecationWarning, lambda: instance.p1, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p2, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p4, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p5, match='^This is deprecated$')
    pytest.warns(DeprecationWarning, lambda: instance.p6, match='^This is deprecated$')

    with pytest.warns(DeprecationWarning, match='^$'):
        instance.p3
