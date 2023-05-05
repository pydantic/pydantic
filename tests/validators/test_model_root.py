from typing import List

import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema


def test_model_root():
    class RootModel:
        __slots__ = 'root'
        root: List[int]

    v = SchemaValidator(
        core_schema.model_schema(RootModel, core_schema.list_schema(core_schema.int_schema()), root_model=True)
    )
    assert repr(v).startswith('SchemaValidator(title="RootModel", validator=Model(\n')

    m = v.validate_python([1, 2, '3'])
    assert isinstance(m, RootModel)
    assert m.root == [1, 2, 3]
    assert not hasattr(m, '__dict__')

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
        __slots__ = 'root'
        root: List[int]

    v = SchemaValidator(
        core_schema.model_schema(
            RootModel, core_schema.list_schema(core_schema.int_schema()), root_model=True, revalidate_instances='always'
        )
    )
    m = v.validate_python([1, '2'])
    assert isinstance(m, RootModel)
    assert m.root == [1, 2]

    m2 = v.validate_python(m)
    assert m2 is not m
    assert isinstance(m2, RootModel)
    assert m2.root == [1, 2]


def test_init():
    class RootModel:
        __slots__ = 'root'
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
        __slots__ = 'root'
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
        __slots__ = 'root'
        root: str

    def f(input_value: str, info):
        call_infos.append(repr(info))
        return input_value + ' validated'

    v = SchemaValidator(
        core_schema.model_schema(
            RootModel, core_schema.field_after_validator_function(f, core_schema.str_schema()), root_model=True
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
