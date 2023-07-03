from typing import List

import pytest

from pydantic_core import PydanticUndefined, SchemaValidator, ValidationError, core_schema


def test_model_root():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: List[int]

    v = SchemaValidator(
        core_schema.model_schema(RootModel, core_schema.list_schema(core_schema.int_schema()), root_model=True)
    )
    assert repr(v).startswith('SchemaValidator(title="RootModel", validator=Model(\n')

    m = v.validate_python([1, 2, '3'])
    assert isinstance(m, RootModel)
    assert m.root == [1, 2, 3]
    assert m.__dict__ == {'root': [1, 2, 3]}

    m = v.validate_json('[1, 2, "3"]')
    assert isinstance(m, RootModel)
    assert m.root == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': 'wrong'}
    ]


def test_revalidate():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: List[int]

    v = SchemaValidator(
        core_schema.model_schema(
            RootModel, core_schema.list_schema(core_schema.int_schema()), root_model=True, revalidate_instances='always'
        )
    )
    m = RootModel()
    m = v.validate_python([1, '2'], self_instance=m)
    assert isinstance(m, RootModel)
    assert m.root == [1, 2]
    assert m.__pydantic_fields_set__ == {'root'}

    m2 = v.validate_python(m)
    assert m2 is not m
    assert isinstance(m2, RootModel)
    assert m2.root == [1, 2]
    assert m.__pydantic_fields_set__ == {'root'}


def test_revalidate_with_default():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: int = 42

    v = SchemaValidator(
        core_schema.model_schema(
            RootModel,
            core_schema.with_default_schema(core_schema.int_schema(), default=42),
            root_model=True,
            revalidate_instances='always',
        )
    )
    m = RootModel()
    m = v.validate_python(PydanticUndefined, self_instance=m)
    assert isinstance(m, RootModel)
    assert m.root == 42
    assert m.__pydantic_fields_set__ == set()

    m2 = v.validate_python(m)
    assert m2 is not m
    assert isinstance(m2, RootModel)
    assert m2.root == 42
    assert m.__pydantic_fields_set__ == set()


def test_init():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: str

    v = SchemaValidator(
        core_schema.model_schema(RootModel, core_schema.str_schema(), root_model=True, revalidate_instances='always')
    )

    m = RootModel()
    ans = v.validate_python('foobar', self_instance=m)
    assert ans is m
    assert ans.root == 'foobar'


def test_assignment():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: str

    v = SchemaValidator(core_schema.model_schema(RootModel, core_schema.str_schema(), root_model=True))

    m = v.validate_python('foobar')
    assert m.root == 'foobar'

    m2 = v.validate_assignment(m, 'root', 'baz')
    assert m2 is m
    assert m.root == 'baz'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'different', 'baz')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('different',),
            'msg': "Object has no attribute 'different'",
            'input': 'baz',
            'ctx': {'attribute': 'different'},
        }
    ]


def test_field_function():
    call_infos = []

    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: str

    def f(input_value: str, info):
        call_infos.append(repr(info))
        return input_value + ' validated'

    v = SchemaValidator(
        core_schema.model_schema(
            RootModel, core_schema.field_after_validator_function(f, 'root', core_schema.str_schema()), root_model=True
        )
    )
    m = v.validate_python('foobar', context='call 1')
    assert isinstance(m, RootModel)
    assert m.root == 'foobar validated'
    assert call_infos == ["ValidationInfo(config=None, context='call 1', field_name='root')"]

    m2 = v.validate_assignment(m, 'root', 'baz', context='assignment call')
    assert m2 is m
    assert m.root == 'baz validated'
    assert call_infos == [
        "ValidationInfo(config=None, context='call 1', field_name='root')",
        "ValidationInfo(config=None, context='assignment call', field_name='root')",
    ]


def test_extra():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: int

    v = SchemaValidator(core_schema.model_schema(RootModel, core_schema.int_schema(), root_model=True))

    m = v.validate_python(1)

    with pytest.raises(AttributeError):
        m.__pydantic_extra__


def test_fields_set():
    assert core_schema.PydanticUndefined is PydanticUndefined

    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: int = 42

    v = SchemaValidator(
        core_schema.model_schema(
            RootModel, core_schema.with_default_schema(core_schema.int_schema(), default=42), root_model=True
        )
    )

    m = RootModel()
    v.validate_python(1, self_instance=m)
    assert m.root == 1
    assert m.__pydantic_fields_set__ == {'root'}

    v.validate_python(PydanticUndefined, self_instance=m)
    assert m.root == 42
    assert m.__pydantic_fields_set__ == set()


def test_construct_from_validate_default():
    class RootModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        root: int

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        value: RootModel = 42

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'value': core_schema.model_field(
                        core_schema.with_default_schema(
                            core_schema.model_schema(RootModel, core_schema.int_schema(), root_model=True),
                            default=42,
                            validate_default=True,
                        )
                    )
                }
            ),
        )
    )

    m = Model()
    v.validate_python({}, self_instance=m)

    assert m.value.root == 42
    assert m.value.__pydantic_fields_set__ == {'root'}
