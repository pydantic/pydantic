import sys
from typing import List

import pytest
from annotated_types import Gt, Lt
from typing_extensions import Annotated

from pydantic import BaseModel, Field
from pydantic.fields import Undefined

NO_VALUE = object()


@pytest.mark.parametrize(
    'hint_fn,value,expected_repr',
    [
        (
            lambda: Annotated[int, Gt(0)],
            5,
            'FieldInfo(annotation=int, required=False, default=5, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: Annotated[int, Field(gt=0)],
            5,
            'FieldInfo(annotation=int, required=False, default=5, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: int,
            Field(5, gt=0),
            'FieldInfo(annotation=int, required=False, default=5, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: int,
            Field(default_factory=lambda: 5, gt=0),
            'FieldInfo(annotation=int, required=False, default_factory=<lambda>, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: Annotated[int, Lt(2)],
            Field(5, gt=0),
            'FieldInfo(annotation=int, required=False, default=5, metadata=[Gt(gt=0), Lt(lt=2)])',
        ),
        (
            lambda: Annotated[int, Gt(0)],
            NO_VALUE,
            'FieldInfo(annotation=int, required=True, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: Annotated[int, Gt(0)],
            Field(),
            'FieldInfo(annotation=int, required=True, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: int,
            Field(gt=0),
            'FieldInfo(annotation=int, required=True, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: Annotated[int, Gt(0)],
            Undefined,
            'FieldInfo(annotation=int, required=True, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: Annotated[int, Field(gt=0), Lt(2)],
            5,
            'FieldInfo(annotation=int, required=False, default=5, metadata=[Gt(gt=0), Lt(lt=2)])',
        ),
    ],
)
def test_annotated(hint_fn, value, expected_repr):
    hint = hint_fn()

    if value is NO_VALUE:

        class M(BaseModel):
            x: hint

    else:

        class M(BaseModel):
            x: hint = value

    assert repr(M.model_fields['x']) == expected_repr


@pytest.mark.parametrize(
    'hint_fn,value,exc_handler',
    [
        (
            lambda: Annotated[int, Field(0)],
            Field(default=5, ge=0),
            pytest.raises(TypeError, match='Field may not be used twice on the same field'),
        ),
        (
            lambda: Annotated[int, Field(0)],
            5,
            pytest.raises(TypeError, match='Default may not be specified twice on the same field'),
        ),
    ],
)
def test_annotated_model_exceptions(hint_fn, value, exc_handler):
    hint = hint_fn()
    with exc_handler:

        class M(BaseModel):
            x: hint = value


@pytest.mark.parametrize('metadata', [0, 'foo'])
def test_annotated_allows_unknown(metadata):
    class M(BaseModel):
        x: Annotated[int, metadata] = 5

    field_info = M.model_fields['x']
    assert len(field_info.metadata) == 1
    assert metadata in field_info.metadata, 'Records the unknown metadata'
    assert metadata in M.__annotations__['x'].__metadata__, 'Annotated type is recorded'


@pytest.mark.parametrize(
    ['hint_fn', 'value', 'empty_init_ctx'],
    [
        (
            lambda: int,
            Undefined,
            pytest.raises(ValueError, match=r'Field required \[type=missing,'),
        ),
        (
            lambda: Annotated[int, Field()],
            Undefined,
            pytest.raises(ValueError, match=r'Field required \[type=missing,'),
        ),
    ],
)
def test_annotated_instance_exceptions(hint_fn, value, empty_init_ctx):
    hint = hint_fn()

    class M(BaseModel):
        x: hint = value

    with empty_init_ctx:
        assert M().x == 5


def test_field_reuse():
    field = Field(description='Long description')

    class Model(BaseModel):
        one: int = field

    assert Model(one=1).model_dump() == {'one': 1}

    class AnnotatedModel(BaseModel):
        one: Annotated[int, field]

    assert AnnotatedModel(one=1).model_dump() == {'one': 1}


def test_config_field_info():
    class Foo(BaseModel):
        a: Annotated[int, Field(description='descr', json_schema_extra={'foobar': 'hello'})]

    assert Foo.model_json_schema(by_alias=True)['properties'] == {
        'a': {'title': 'A', 'description': 'descr', 'foobar': 'hello', 'type': 'integer'},
    }


@pytest.mark.skipif(sys.version_info < (3, 10), reason='repr different on older versions')
def test_annotated_alias() -> None:
    # https://github.com/pydantic/pydantic/issues/2971

    StrAlias = Annotated[str, Field(max_length=3)]
    IntAlias = Annotated[int, Field(default_factory=lambda: 2)]

    Nested = Annotated[List[StrAlias], Field(description='foo')]

    class MyModel(BaseModel):
        a: StrAlias = 'abc'
        b: StrAlias
        c: IntAlias
        d: IntAlias
        e: Nested

    fields_repr = {k: repr(v) for k, v in MyModel.model_fields.items()}
    assert fields_repr == {
        'a': "FieldInfo(annotation=str, required=False, default='abc', metadata=[MaxLen(max_length=3)])",
        'b': 'FieldInfo(annotation=str, required=True, metadata=[MaxLen(max_length=3)])',
        'c': 'FieldInfo(annotation=int, required=False, default_factory=<lambda>)',
        'd': 'FieldInfo(annotation=int, required=False, default_factory=<lambda>)',
        'e': (
            'FieldInfo(annotation=List[Annotated[str, FieldInfo(annotation=NoneType, required=True, metadata=[MaxLe'
            "n(max_length=3)])]], required=True, description='foo')"
        ),
    }
    assert MyModel(b='def', e=['xyz']).model_dump() == dict(a='abc', b='def', c=2, d=2, e=['xyz'])
