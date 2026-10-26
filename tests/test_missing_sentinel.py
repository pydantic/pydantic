import pickle
from typing import Annotated, Literal, Union

import pytest
import typing_extensions
from annotated_types import Ge
from pydantic_core import PydanticSerializationUnexpectedValue

from pydantic import MISSING, BaseModel, Field, PydanticDeprecatedSince214, TypeAdapter, ValidationError


def test_missing_sentinel_model() -> None:
    class Model(BaseModel):
        f: int | MISSING = MISSING
        g: MISSING = MISSING

    m1 = Model()

    assert m1.model_dump() == {}
    assert m1.model_dump_json() == '{}'

    m2 = Model.model_validate({'f': MISSING, 'g': MISSING})

    assert m2.f is MISSING
    assert m2.g is MISSING

    m3 = Model(f=1)

    assert m3.model_dump() == {'f': 1}
    assert m3.model_dump_json() == '{"f":1}'


def test_missing_sentinel_type_adapter() -> None:
    """Note that this usage isn't explicitly supported (and useless in practice)."""

    ta = TypeAdapter(MISSING)

    assert ta.validate_python(MISSING) is MISSING

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1)

    assert exc_info.value.errors()[0]['type'] == 'missing_sentinel_error'

    assert ta.dump_python(MISSING) is MISSING

    with pytest.raises(PydanticSerializationUnexpectedValue):
        ta.dump_python(1)


# Defined in module to be picklable:
class ModelPickle(BaseModel):
    f: int | MISSING = MISSING


def test_missing_sentinel_pickle() -> None:
    m = ModelPickle()
    m_reconstructed = pickle.loads(pickle.dumps(m))

    assert m_reconstructed.f is MISSING


def test_missing_sentinel_json_schema() -> None:
    class Model(BaseModel):
        f: int | MISSING = MISSING
        g: MISSING = MISSING
        h: MISSING

    assert Model.model_json_schema()['properties'] == {
        'f': {'title': 'F', 'type': 'integer'},
    }


def test_model_construct_with_missing_default_does_not_crash() -> None:
    class M(BaseModel):
        a: int | MISSING = MISSING

    # Should not raise
    m = M.model_construct()
    assert hasattr(m, 'a')
    # Keep sentinel by identity
    assert getattr(m, 'a') is MISSING


def test_no_warning_when_excluded_in_nested_model() -> None:
    """https://github.com/pydantic/pydantic/issues/12628"""

    class Inner(BaseModel):
        f1: int | MISSING = MISSING
        f2: int | MISSING = MISSING

    class Outer(BaseModel):
        inner: Inner | MISSING = MISSING

    s = Outer(
        inner={'f1': 1},
    )

    # Shouldn't raise a serialization warning about missing fields:
    assert s.model_dump() == {'inner': {'f1': 1}}


def test_missing_sentinel_constraints_pushdown() -> None:
    class Model(BaseModel):
        f1: Annotated[int | MISSING, Ge(1)] = MISSING
        f2: Annotated[MISSING | int, Ge(1)] = MISSING
        f3: Annotated[int | str | MISSING, Ge(1)] = MISSING
        f4: Annotated[int | str | None | MISSING, Ge(1)] = MISSING

    js_schema = Model.model_json_schema()

    assert js_schema['properties']['f1'] == {'minimum': 1, 'title': 'F1', 'type': 'integer'}
    assert js_schema['properties']['f2'] == {'minimum': 1, 'title': 'F2', 'type': 'integer'}
    # Note: 'ge' is still wrong (see https://github.com/pydantic/pydantic/issues/11576)
    assert js_schema['properties']['f3'] == {'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'ge': 1, 'title': 'F3'}
    assert js_schema['properties']['f4'] == {
        'anyOf': [{'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'ge': 1}, {'type': 'null'}],
        'title': 'F4',
    }


def test_missing_sentinel_child_fields() -> None:
    """https://github.com/pydantic/pydantic/issues/13001."""

    class Base(BaseModel, extra='forbid'):
        base_field: str | MISSING = MISSING

    class Parent(Base):
        parent_field: str

    class Child(Parent):
        child_field: str

    class Container(BaseModel, extra='forbid'):
        item: Parent | MISSING = MISSING

    child = Child(parent_field='p', child_field='c')
    container = Container(item=child)

    result = TypeAdapter(Container).dump_python(container)

    assert result == {'item': {'parent_field': 'p'}}


def test_missing_sentinel_validation_error_not_mentioned() -> None:
    class Model(BaseModel):
        f1: int | MISSING = MISSING
        f2: int | None | MISSING = MISSING
        f3: int | str | MISSING = MISSING

    with pytest.raises(ValidationError) as exc_info:
        Model(f1='not_an_int', f2='not_an_int', f3=[])

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('f1',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_an_int',
        },
        {
            'type': 'int_parsing',
            'loc': ('f2',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_an_int',
        },
        {
            'type': 'int_type',
            'loc': ('f3', 'int'),
            'msg': 'Input should be a valid integer',
            'input': [],
        },
        {
            'type': 'string_type',
            'loc': ('f3', 'str'),
            'msg': 'Input should be a valid string',
            'input': [],
        },
    ]


def test_missing_sentinel_discriminated_union() -> None:
    class Cat(BaseModel):
        kind: Literal['cat']

    class Dog(BaseModel):
        kind: Literal['dog']

    MissingCat = typing_extensions.TypeAliasType('MissingCat', Cat | MISSING)

    class Model(BaseModel):
        pet1: Annotated[Cat | Dog | MISSING, Field(discriminator='kind')] = MISSING
        pet2: Annotated[Cat | Dog | None | MISSING, Field(discriminator='kind')] = MISSING
        # The inner `Annotated` form prevents the union from being flattened, so that the
        # 'missing-sentinel' schema is a choice of the outer union:
        pet3: Annotated[
            Union[Annotated[Cat | MISSING, Field(title='Cat')], Dog],  # noqa: UP007
            Field(discriminator='kind'),
        ] = MISSING
        # The 'missing-sentinel' schema is referenced through a 'definition-ref' schema:
        pet4: Annotated[Union[MissingCat, Dog], Field(discriminator='kind')] = MISSING  # noqa: UP007

    m = Model(pet1={'kind': 'cat'}, pet2=None, pet3={'kind': 'dog'}, pet4={'kind': 'cat'})
    assert isinstance(m.pet1, Cat)
    assert m.pet2 is None
    assert isinstance(m.pet3, Dog)
    assert isinstance(m.pet4, Cat)

    m = Model(pet1=MISSING, pet2=MISSING, pet3=MISSING, pet4=MISSING)
    assert m.model_dump() == {}

    with pytest.raises(ValidationError) as exc_info:
        Model(pet1={'kind': 'fish'})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'union_tag_invalid',
            'loc': ('pet1',),
            'msg': "Input tag 'fish' found using 'kind' does not match any of the expected tags: 'cat', 'dog'",
            'input': {'kind': 'fish'},
            'ctx': {'discriminator': "'kind'", 'tag': 'fish', 'expected_tags': "'cat', 'dog'"},
        },
    ]

    json_schema = Model.model_json_schema()
    tagged_union_json_schema = {
        'discriminator': {'mapping': {'cat': '#/$defs/Cat', 'dog': '#/$defs/Dog'}, 'propertyName': 'kind'},
        'oneOf': [{'$ref': '#/$defs/Cat'}, {'$ref': '#/$defs/Dog'}],
    }
    assert json_schema['properties'] == {
        'pet1': {**tagged_union_json_schema, 'title': 'Pet1'},
        'pet2': {'anyOf': [tagged_union_json_schema, {'type': 'null'}], 'title': 'Pet2'},
        'pet3': {**tagged_union_json_schema, 'title': 'Pet3'},
        'pet4': {
            'discriminator': {'mapping': {'cat': '#/$defs/MissingCat', 'dog': '#/$defs/Dog'}, 'propertyName': 'kind'},
            'oneOf': [{'$ref': '#/$defs/MissingCat'}, {'$ref': '#/$defs/Dog'}],
            'title': 'Pet4',
        },
    }


def test_missing_sentinel_none_union() -> None:
    class Model(BaseModel):
        f: None | MISSING = MISSING

    assert Model(f=None).f is None
    assert Model(f=MISSING).f is MISSING
    assert Model().model_dump() == {}
    assert Model(f=None).model_dump() == {'f': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(f=1)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'none_required',
            'loc': ('f',),
            'msg': 'Input should be None',
            'input': 1,
        },
    ]

    assert Model.model_json_schema()['properties']['f'] == {'title': 'F', 'type': 'null'}


def test_missing_sentinel_nested_type() -> None:
    ta = TypeAdapter(list[int | MISSING])

    assert ta.validate_python([1, MISSING]) == [1, MISSING]
    assert ta.dump_python([1, MISSING]) == [1, MISSING]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 'not_an_int'])

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_an_int',
        },
    ]


def test_missing_sentinel_experimental_import_deprecated() -> None:
    import pydantic.experimental.missing_sentinel as experimental_module

    with pytest.warns(PydanticDeprecatedSince214, match='The `MISSING` sentinel is no longer experimental'):
        assert experimental_module.MISSING is MISSING
