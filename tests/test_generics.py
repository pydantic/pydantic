import gc
import itertools
import json
import sys
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pytest
from typing_extensions import Annotated, Literal

from pydantic import BaseModel, Field, Json, ValidationError, create_model, root_validator, validator
from pydantic.generics import (
    GenericModel,
    _assigned_parameters,
    _generic_types_cache,
    iter_contained_typevars,
    replace_types,
)


@pytest.fixture(autouse=True)
def clean_cache():
    gc.collect()  # cleans up _generic_types_cache for checking item counts in the cache


def test_generic_name():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    if sys.version_info >= (3, 9):
        assert Result[list[int]].__name__ == 'Result[list[int]]'
    assert Result[List[int]].__name__ == 'Result[List[int]]'
    assert Result[int].__name__ == 'Result[int]'


def test_double_parameterize_error():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    with pytest.raises(TypeError) as exc_info:
        Result[int][int]

    assert str(exc_info.value) == 'Cannot parameterize a concrete instantiation of a generic model'


def test_value_validation():
    T = TypeVar('T')

    class Response(GenericModel, Generic[T]):
        data: T

        @validator('data', each_item=True)
        def validate_value_nonzero(cls, v):
            if v == 0:
                raise ValueError('value is zero')
            return v

        @root_validator()
        def validate_sum(cls, values):
            if sum(values.get('data', {}).values()) > 5:
                raise ValueError('sum too large')
            return values

    assert Response[Dict[int, int]](data={1: '4'}).dict() == {'data': {1: 4}}
    with pytest.raises(ValidationError) as exc_info:
        Response[Dict[int, int]](data={1: 'a'})
    assert exc_info.value.errors() == [
        {'loc': ('data', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Response[Dict[int, int]](data={1: 0})
    assert exc_info.value.errors() == [{'loc': ('data', 1), 'msg': 'value is zero', 'type': 'value_error'}]

    with pytest.raises(ValidationError) as exc_info:
        Response[Dict[int, int]](data={1: 3, 2: 6})
    assert exc_info.value.errors() == [{'loc': ('__root__',), 'msg': 'sum too large', 'type': 'value_error'}]


def test_methods_are_inherited():
    class CustomGenericModel(GenericModel):
        def method(self):
            return self.data

    T = TypeVar('T')

    class Model(CustomGenericModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    assert instance.method() == 1


def test_config_is_inherited():
    class CustomGenericModel(GenericModel):
        class Config:
            allow_mutation = False

    T = TypeVar('T')

    class Model(CustomGenericModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    with pytest.raises(TypeError) as exc_info:
        instance.data = 2

    assert str(exc_info.value) == '"Model[int]" is immutable and does not support item assignment'


def test_default_argument():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T
        other: bool = True

    result = Result[int](data=1)
    assert result.other is True


def test_default_argument_for_typevar():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T = 4

    result = Result[int]()
    assert result.data == 4

    result = Result[float]()
    assert result.data == 4

    result = Result[int](data=1)
    assert result.data == 1


def test_classvar():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T
        other: ClassVar[int] = 1

    assert Result.other == 1
    assert Result[int].other == 1
    assert Result[int](data=1).other == 1
    assert 'other' not in Result.__fields__


def test_non_annotated_field():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T
        other = True

    assert 'other' in Result.__fields__
    assert 'other' in Result[int].__fields__

    result = Result[int](data=1)
    assert result.other is True


def test_must_inherit_from_generic():
    with pytest.raises(TypeError) as exc_info:

        class Result(GenericModel):
            pass

        Result[int]

    assert str(exc_info.value) == 'Type Result must inherit from typing.Generic before being parameterized'


def test_parameters_placed_on_generic():
    T = TypeVar('T')
    with pytest.raises(TypeError, match='Type parameters should be placed on typing.Generic, not GenericModel'):

        class Result(GenericModel[T]):
            pass


def test_parameters_must_be_typevar():
    with pytest.raises(TypeError, match='Type GenericModel must inherit from typing.Generic before being '):

        class Result(GenericModel[int]):
            pass


def test_subclass_can_be_genericized():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        pass

    Result[T]


def test_parameter_count():
    T = TypeVar('T')
    S = TypeVar('S')

    class Model(GenericModel, Generic[T, S]):
        x: T
        y: S

    with pytest.raises(TypeError) as exc_info:
        Model[int, int, int]
    assert str(exc_info.value) == 'Too many parameters for Model; actual 3, expected 2'

    with pytest.raises(TypeError) as exc_info:
        Model[int]
    assert str(exc_info.value) == 'Too few parameters for Model; actual 1, expected 2'


def test_cover_cache():
    cache_size = len(_generic_types_cache)
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        x: T

    models = []  # keep references to models to get cache size

    models.append(Model[int])  # adds both with-tuple and without-tuple version to cache
    assert len(_generic_types_cache) == cache_size + 2
    models.append(Model[int])  # uses the cache
    assert len(_generic_types_cache) == cache_size + 2
    del models


def test_cache_keys_are_hashable():
    cache_size = len(_generic_types_cache)
    T = TypeVar('T')
    C = Callable[[str, Dict[str, Any]], Iterable[str]]

    class MyGenericModel(GenericModel, Generic[T]):
        t: T

    # Callable's first params get converted to a list, which is not hashable.
    # Make sure we can handle that special case
    Simple = MyGenericModel[Callable[[int], str]]
    models = []  # keep references to models to get cache size
    models.append(Simple)
    assert len(_generic_types_cache) == cache_size + 2
    # Nested Callables
    models.append(MyGenericModel[Callable[[C], Iterable[str]]])
    assert len(_generic_types_cache) == cache_size + 4
    models.append(MyGenericModel[Callable[[Simple], Iterable[int]]])
    assert len(_generic_types_cache) == cache_size + 6
    models.append(MyGenericModel[Callable[[MyGenericModel[C]], Iterable[int]]])
    assert len(_generic_types_cache) == cache_size + 10

    class Model(BaseModel):
        x: MyGenericModel[Callable[[C], Iterable[str]]] = Field(...)

    models.append(Model)
    assert len(_generic_types_cache) == cache_size + 10
    del models


def test_caches_get_cleaned_up():
    types_cache_size = len(_generic_types_cache)
    params_cache_size = len(_assigned_parameters)
    T = TypeVar('T')

    class MyGenericModel(GenericModel, Generic[T]):
        x: T

    Model = MyGenericModel[int]
    assert len(_generic_types_cache) == types_cache_size + 2
    assert len(_assigned_parameters) == params_cache_size + 1
    del Model
    gc.collect()
    assert len(_generic_types_cache) == types_cache_size
    assert len(_assigned_parameters) == params_cache_size


def test_generics_work_with_many_parametrized_base_models():
    cache_size = len(_generic_types_cache)
    params_size = len(_assigned_parameters)
    count_create_models = 1000
    T = TypeVar('T')
    C = TypeVar('C')

    class A(GenericModel, Generic[T, C]):
        x: T
        y: C

    class B(A[int, C], GenericModel, Generic[C]):
        pass

    models = [create_model(f'M{i}') for i in range(count_create_models)]
    generics = []
    for m in models:
        Working = B[m]
        generics.append(Working)

    assert len(_generic_types_cache) == cache_size + count_create_models * 5 + 1
    assert len(_assigned_parameters) == params_size + count_create_models * 3 + 1
    del models
    del generics


def test_generic_config():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

        class Config:
            allow_mutation = False

    result = Result[int](data=1)
    assert result.data == 1
    with pytest.raises(TypeError):
        result.data = 2


def test_enum_generic():
    T = TypeVar('T')

    class MyEnum(Enum):
        x = 1
        y = 2

    class Model(GenericModel, Generic[T]):
        enum: T

    Model[MyEnum](enum=MyEnum.x)
    Model[MyEnum](enum=2)


def test_generic():
    data_type = TypeVar('data_type')
    error_type = TypeVar('error_type')

    class Result(GenericModel, Generic[data_type, error_type]):
        data: Optional[List[data_type]]
        error: Optional[error_type]
        positive_number: int

        @validator('error', always=True)
        def validate_error(cls, v: Optional[error_type], values: Dict[str, Any]) -> Optional[error_type]:
            if values.get('data', None) is None and v is None:
                raise ValueError('Must provide data or error')
            if values.get('data', None) is not None and v is not None:
                raise ValueError('Must not provide both data and error')
            return v

        @validator('positive_number')
        def validate_positive_number(cls, v: int) -> int:
            if v < 0:
                raise ValueError
            return v

    class Error(BaseModel):
        message: str

    class Data(BaseModel):
        number: int
        text: str

    success1 = Result[Data, Error](data=[Data(number=1, text='a')], positive_number=1)
    assert success1.dict() == {'data': [{'number': 1, 'text': 'a'}], 'error': None, 'positive_number': 1}
    assert repr(success1) == "Result[Data, Error](data=[Data(number=1, text='a')], error=None, positive_number=1)"

    success2 = Result[Data, Error](error=Error(message='error'), positive_number=1)
    assert success2.dict() == {'data': None, 'error': {'message': 'error'}, 'positive_number': 1}
    assert repr(success2) == "Result[Data, Error](data=None, error=Error(message='error'), positive_number=1)"
    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](error=Error(message='error'), positive_number=-1)
    assert exc_info.value.errors() == [{'loc': ('positive_number',), 'msg': '', 'type': 'value_error'}]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text='a')], error=Error(message='error'), positive_number=1)
    assert exc_info.value.errors() == [
        {'loc': ('error',), 'msg': 'Must not provide both data and error', 'type': 'value_error'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text='a')], error=Error(message='error'), positive_number=1)
    assert exc_info.value.errors() == [
        {'loc': ('error',), 'msg': 'Must not provide both data and error', 'type': 'value_error'}
    ]


def test_alongside_concrete_generics():
    from pydantic.generics import GenericModel

    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        item: T
        metadata: Dict[str, Any]

    model = MyModel[int](item=1, metadata={})
    assert model.item == 1
    assert model.metadata == {}


def test_complex_nesting():
    from pydantic.generics import GenericModel

    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        item: List[Dict[Union[int, T], str]]

    item = [{1: 'a', 'a': 'a'}]
    model = MyModel[str](item=item)
    assert model.item == item


def test_required_value():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        MyModel[int]()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_optional_value():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        a: Optional[int] = 1

    model = MyModel[int]()
    assert model.dict() == {'a': 1}


def test_custom_schema():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        a: int = Field(1, description='Custom')

    schema = MyModel[int].schema()
    assert schema['properties']['a'].get('description') == 'Custom'


def test_child_schema():
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        a: T

    class Child(Model[T], Generic[T]):
        pass

    schema = Child[int].schema()
    assert schema == {
        'title': 'Child[int]',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
    }


def test_custom_generic_naming():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        value: Optional[T]

        @classmethod
        def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
            param_names = [param.__name__ if hasattr(param, '__name__') else str(param) for param in params]
            title = param_names[0].title()
            return f'Optional{title}Wrapper'

    assert repr(MyModel[int](value=1)) == 'OptionalIntWrapper(value=1)'
    assert repr(MyModel[str](value=None)) == 'OptionalStrWrapper(value=None)'


def test_nested():
    AT = TypeVar('AT')

    class InnerT(GenericModel, Generic[AT]):
        a: AT

    inner_int = InnerT[int](a=8)
    inner_str = InnerT[str](a='ate')
    inner_dict_any = InnerT[Any](a={})
    inner_int_any = InnerT[Any](a=7)

    class OuterT_SameType(GenericModel, Generic[AT]):
        i: InnerT[AT]

    OuterT_SameType[int](i=inner_int)
    OuterT_SameType[str](i=inner_str)
    OuterT_SameType[int](i=inner_int_any)  # ensure parsing the broader inner type works

    with pytest.raises(ValidationError) as exc_info:
        OuterT_SameType[int](i=inner_str)
    assert exc_info.value.errors() == [
        {'loc': ('i', 'a'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        OuterT_SameType[int](i=inner_dict_any)
    assert exc_info.value.errors() == [
        {'loc': ('i', 'a'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_partial_specification():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(GenericModel, Generic[AT, BT]):
        a: AT
        b: BT

    partial_model = Model[int, BT]
    concrete_model = partial_model[str]
    concrete_model(a=1, b='abc')
    with pytest.raises(ValidationError) as exc_info:
        concrete_model(a='abc', b=None)
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('b',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
    ]


def test_partial_specification_with_inner_typevar():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(GenericModel, Generic[AT, BT]):
        a: List[AT]
        b: List[BT]

    partial_model = Model[str, BT]
    assert partial_model.__concrete__ is False
    concrete_model = partial_model[int]
    assert concrete_model.__concrete__ is True

    # nested resolution of partial models should work as expected
    nested_resolved = concrete_model(a=[123], b=['456'])
    assert nested_resolved.a == ['123']
    assert nested_resolved.b == [456]


def test_partial_specification_name():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(GenericModel, Generic[AT, BT]):
        a: AT
        b: BT

    partial_model = Model[int, BT]
    assert partial_model.__name__ == 'Model[int, BT]'
    concrete_model = partial_model[str]
    assert concrete_model.__name__ == 'Model[int, BT][str]'


def test_partial_specification_instantiation():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(GenericModel, Generic[AT, BT]):
        a: AT
        b: BT

    partial_model = Model[int, BT]
    partial_model(a=1, b=2)

    partial_model(a=1, b='a')

    with pytest.raises(ValidationError) as exc_info:
        partial_model(a='a', b=2)
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_partial_specification_instantiation_bounded():
    AT = TypeVar('AT')
    BT = TypeVar('BT', bound=int)

    class Model(GenericModel, Generic[AT, BT]):
        a: AT
        b: BT

    Model(a=1, b=1)
    with pytest.raises(ValidationError) as exc_info:
        Model(a=1, b='a')
    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    partial_model = Model[int, BT]
    partial_model(a=1, b=1)
    with pytest.raises(ValidationError) as exc_info:
        partial_model(a=1, b='a')
    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_typevar_parametrization():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(GenericModel, Generic[AT, BT]):
        a: AT
        b: BT

    CT = TypeVar('CT', bound=int)
    DT = TypeVar('DT', bound=int)

    with pytest.raises(ValidationError) as exc_info:
        Model[CT, DT](a='a', b='b')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_multiple_specification():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(GenericModel, Generic[AT, BT]):
        a: AT
        b: BT

    CT = TypeVar('CT')
    partial_model = Model[CT, CT]
    concrete_model = partial_model[str]

    with pytest.raises(ValidationError) as exc_info:
        concrete_model(a=None, b=None)
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
        {'loc': ('b',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
    ]


def test_generic_subclass_of_concrete_generic():
    T = TypeVar('T')
    U = TypeVar('U')

    class GenericBaseModel(GenericModel, Generic[T]):
        data: T

    class GenericSub(GenericBaseModel[int], Generic[U]):
        extra: U

    ConcreteSub = GenericSub[int]

    with pytest.raises(ValidationError):
        ConcreteSub(data=2, extra='wrong')

    with pytest.raises(ValidationError):
        ConcreteSub(data='wrong', extra=2)

    ConcreteSub(data=2, extra=3)


def test_generic_model_pickle(create_module):
    # Using create_module because pickle doesn't support
    # objects with <locals> in their __qualname__  (e. g. defined in function)
    @create_module
    def module():
        import pickle
        from typing import Generic, TypeVar

        from pydantic import BaseModel
        from pydantic.generics import GenericModel

        t = TypeVar('t')

        class Model(BaseModel):
            a: float
            b: int = 10

        class MyGeneric(GenericModel, Generic[t]):
            value: t

        original = MyGeneric[Model](value=Model(a='24'))
        dumped = pickle.dumps(original)
        loaded = pickle.loads(dumped)
        assert loaded.value.a == original.value.a == 24
        assert loaded.value.b == original.value.b == 10
        assert loaded == original


def test_generic_model_from_function_pickle_fail(create_module):
    @create_module
    def module():
        import pickle
        from typing import Generic, TypeVar

        import pytest

        from pydantic import BaseModel
        from pydantic.generics import GenericModel

        t = TypeVar('t')

        class Model(BaseModel):
            a: float
            b: int = 10

        class MyGeneric(GenericModel, Generic[t]):
            value: t

        def get_generic(t):
            return MyGeneric[t]

        original = get_generic(Model)(value=Model(a='24'))
        with pytest.raises(pickle.PicklingError):
            pickle.dumps(original)


def test_generic_model_redefined_without_cache_fail(create_module, monkeypatch):
    # match identity checker otherwise we never get to the redefinition check
    monkeypatch.setattr('pydantic.generics.all_identical', lambda left, right: False)

    @create_module
    def module():
        from typing import Generic, TypeVar

        from pydantic import BaseModel
        from pydantic.generics import GenericModel, _generic_types_cache

        t = TypeVar('t')

        class MyGeneric(GenericModel, Generic[t]):
            value: t

        class Model(BaseModel):
            ...

        concrete = MyGeneric[Model]
        _generic_types_cache.clear()
        second_concrete = MyGeneric[Model]

        class Model(BaseModel):  # same name, but type different, so it's not in cache
            ...

        third_concrete = MyGeneric[Model]
        assert concrete is not second_concrete
        assert concrete is not third_concrete
        assert second_concrete is not third_concrete
        assert globals()['MyGeneric[Model]'] is concrete
        assert globals()['MyGeneric[Model]_'] is second_concrete
        assert globals()['MyGeneric[Model]__'] is third_concrete


def test_generic_model_caching_detect_order_of_union_args_basic(create_module):
    # Basic variant of https://github.com/pydantic/pydantic/issues/4474
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic.generics import GenericModel

        t = TypeVar('t')

        class Model(GenericModel, Generic[t]):
            data: t

        int_or_float_model = Model[Union[int, float]]
        float_or_int_model = Model[Union[float, int]]

        assert type(int_or_float_model(data='1').data) is int
        assert type(float_or_int_model(data='1').data) is float


@pytest.mark.skipif(sys.version_info < (3, 10), reason='pep-604 syntax (Ex.: list | int) was added in python3.10')
def test_generic_model_caching_detect_order_of_union_args_basic_with_pep_604_syntax(create_module):
    # Basic variant of https://github.com/pydantic/pydantic/issues/4474 with pep-604 syntax.
    @create_module
    def module():
        from typing import Generic, TypeVar

        from pydantic.generics import GenericModel

        t = TypeVar('t')

        class Model(GenericModel, Generic[t]):
            data: t

        int_or_float_model = Model[int | float]
        float_or_int_model = Model[float | int]

        assert type(int_or_float_model(data='1').data) is int
        assert type(float_or_int_model(data='1').data) is float


@pytest.mark.skip(
    reason="""
Depends on similar issue in CPython itself: https://github.com/python/cpython/issues/86483
Documented and skipped for possible fix later.
"""
)
def test_generic_model_caching_detect_order_of_union_args_nested(create_module):
    # Nested variant of https://github.com/pydantic/pydantic/issues/4474
    @create_module
    def module():
        from typing import Generic, List, TypeVar, Union

        from pydantic.generics import GenericModel

        t = TypeVar('t')

        class Model(GenericModel, Generic[t]):
            data: t

        int_or_float_model = Model[List[Union[int, float]]]
        float_or_int_model = Model[List[Union[float, int]]]

        assert type(int_or_float_model(data=['1']).data[0]) is int
        assert type(float_or_int_model(data=['1']).data[0]) is float


def test_get_caller_frame_info(create_module):
    @create_module
    def module():
        from pydantic.generics import get_caller_frame_info

        def function():
            assert get_caller_frame_info() == (__name__, True)

            another_function()

        def another_function():
            assert get_caller_frame_info() == (__name__, False)
            third_function()

        def third_function():
            assert get_caller_frame_info() == (__name__, False)

        function()


def test_get_caller_frame_info_called_from_module(create_module):
    @create_module
    def module():
        from unittest.mock import patch

        import pytest

        from pydantic.generics import get_caller_frame_info

        with pytest.raises(RuntimeError, match='This function must be used inside another function'):
            with patch('sys._getframe', side_effect=ValueError('getframe_exc')):
                get_caller_frame_info()


def test_get_caller_frame_info_when_sys_getframe_undefined():
    from pydantic.generics import get_caller_frame_info

    getframe = sys._getframe
    del sys._getframe
    try:
        assert get_caller_frame_info() == (None, False)
    finally:  # just to make sure we always setting original attribute back
        sys._getframe = getframe


def test_iter_contained_typevars():
    T = TypeVar('T')
    T2 = TypeVar('T2')

    class Model(GenericModel, Generic[T]):
        a: T

    assert list(iter_contained_typevars(Model[T])) == [T]
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[T]]]])) == [T]
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[int]]]])) == []
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[T], Callable[[T2, T], str]]]])) == [T, T2, T]


def test_nested_identity_parameterization():
    T = TypeVar('T')
    T2 = TypeVar('T2')

    class Model(GenericModel, Generic[T]):
        a: T

    assert Model[T][T][T] is Model
    assert Model[T] is Model
    assert Model[T2] is not Model


def test_replace_types():
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        a: T

    assert replace_types(T, {T: int}) is int
    assert replace_types(List[Union[str, list, T]], {T: int}) == List[Union[str, list, int]]
    assert replace_types(Callable, {T: int}) == Callable
    assert replace_types(Callable[[int, str, T], T], {T: int}) == Callable[[int, str, int], int]
    assert replace_types(T, {}) is T
    assert replace_types(Model[List[T]], {T: int}) == Model[List[T]][int]
    assert replace_types(T, {}) is T
    assert replace_types(Type[T], {T: int}) == Type[int]
    assert replace_types(Model[T], {T: T}) == Model[T]

    if sys.version_info >= (3, 9):
        # Check generic aliases (subscripted builtin types) to make sure they
        # resolve correctly (don't get translated to typing versions for
        # example)
        assert replace_types(list[Union[str, list, T]], {T: int}) == list[Union[str, list, int]]


@pytest.mark.skipif(sys.version_info < (3, 10), reason='pep-604 syntax (Ex.: list | int) was added in python3.10')
def test_replace_types_with_pep_604_syntax() -> None:
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        a: T

    assert replace_types(T | None, {T: int}) == int | None
    assert replace_types(T | int | str, {T: float}) == float | int | str
    assert replace_types(list[T] | None, {T: int}) == list[int] | None
    assert replace_types(List[str | list | T], {T: int}) == List[str | list | int]
    assert replace_types(list[str | list | T], {T: int}) == list[str | list | int]
    assert replace_types(list[str | list | list[T]], {T: int}) == list[str | list | list[int]]
    assert replace_types(list[Model[T] | None] | None, {T: T}) == list[Model[T] | None] | None
    assert (
        replace_types(T | list[T | list[T | list[T | None] | None] | None] | None, {T: int})
        == int | list[int | list[int | list[int | None] | None] | None] | None
    )
    assert replace_types(list[list[list[T | None]]], {T: int}) == list[list[list[int | None]]]


def test_replace_types_with_user_defined_generic_type_field():
    """Test that using user defined generic types as generic model fields are handled correctly."""

    T = TypeVar('T')
    KT = TypeVar('KT')
    VT = TypeVar('VT')

    class GenericMapping(Mapping[KT, VT]):
        pass

    class GenericList(List[T]):
        pass

    class Model(GenericModel, Generic[T, KT, VT]):
        map_field: GenericMapping[KT, VT]
        list_field: GenericList[T]

    assert replace_types(Model, {T: bool, KT: str, VT: int}) == Model[bool, str, int]
    assert replace_types(Model[T, KT, VT], {T: bool, KT: str, VT: int}) == Model[bool, str, int]
    assert replace_types(Model[T, VT, KT], {T: bool, KT: str, VT: int}) == Model[T, VT, KT][bool, int, str]


def test_replace_types_identity_on_unchanged():
    T = TypeVar('T')
    U = TypeVar('U')

    type_ = List[Union[str, Callable[[list], Optional[str]], U]]
    assert replace_types(type_, {T: int}) is type_


def test_deep_generic():
    T = TypeVar('T')
    S = TypeVar('S')
    R = TypeVar('R')

    class OuterModel(GenericModel, Generic[T, S, R]):
        a: Dict[R, Optional[List[T]]]
        b: Optional[Union[S, R]]
        c: R
        d: float

    class InnerModel(GenericModel, Generic[T, R]):
        c: T
        d: R

    class NormalModel(BaseModel):
        e: int
        f: str

    inner_model = InnerModel[int, str]
    generic_model = OuterModel[inner_model, NormalModel, int]

    inner_models = [inner_model(c=1, d='a')]
    generic_model(a={1: inner_models, 2: None}, b=None, c=1, d=1.5)
    generic_model(a={}, b=NormalModel(e=1, f='a'), c=1, d=1.5)
    generic_model(a={}, b=1, c=1, d=1.5)

    assert InnerModel.__concrete__ is False
    assert inner_model.__concrete__ is True


@pytest.mark.skipif(sys.version_info < (3, 10), reason='pep-604 syntax (Ex.: list | int) was added in python3.10')
def test_wrapping_resolved_generic_with_pep_604_syntax() -> None:
    T = TypeVar('T')

    class InnerModel(GenericModel, Generic[T]):
        generic: list[T] | None

    class OuterModel(BaseModel):
        wrapper: InnerModel[int]

    with pytest.raises(ValidationError):
        OuterModel(wrapper={'generic': ['string_instead_of_int']})
    assert OuterModel(wrapper={'generic': [1]}).dict() == {'wrapper': {'generic': [1]}}


@pytest.mark.skipif(sys.version_info < (3, 10), reason='pep-604 syntax (Ex.: list | int) was added in python3.10')
def test_type_propagation_in_deep_generic_with_pep_604_syntax() -> None:
    T = TypeVar('T')

    class InnerModel(GenericModel, Generic[T]):
        generic: list[T] | None

    class OuterModel(GenericModel, Generic[T]):
        wrapper: InnerModel[T] | None

    with pytest.raises(ValidationError):
        OuterModel[int](wrapper={'generic': ['string_instead_of_int']})
    assert OuterModel[int](wrapper={'generic': [1]}) == {'wrapper': {'generic': [1]}}


@pytest.mark.skipif(sys.version_info < (3, 10), reason='pep-604 syntax (Ex.: list | int) was added in python3.10')
def test_deep_generic_with_pep_604_syntax() -> None:
    T = TypeVar('T')
    S = TypeVar('S')
    R = TypeVar('R')

    class OuterModel(GenericModel, Generic[T, S, R]):
        a: Dict[R, list[T] | None]
        b: S | R | None
        c: R
        d: float

    class InnerModel(GenericModel, Generic[T, R]):
        c: list[T] | None
        d: list[R] | None

    class NormalModel(BaseModel):
        e: int
        f: str

    inner_model = InnerModel[int, str]
    generic_model = OuterModel[inner_model, NormalModel, int]

    inner_models = [inner_model(c=[1], d=['a'])]
    generic_model(a={1: inner_models, 2: None}, b=None, c=1, d=1.5)
    generic_model(a={}, b=NormalModel(e=1, f='a'), c=1, d=1.5)
    generic_model(a={}, b=1, c=1, d=1.5)

    assert InnerModel.__concrete__ is False
    assert inner_model.__concrete__ is True


def test_deep_generic_with_inner_typevar():
    T = TypeVar('T')

    class OuterModel(GenericModel, Generic[T]):
        a: List[T]

    class InnerModel(OuterModel[T], Generic[T]):
        pass

    assert InnerModel[int].__concrete__ is True
    assert InnerModel.__concrete__ is False

    with pytest.raises(ValidationError):
        InnerModel[int](a=['wrong'])
    assert InnerModel[int](a=['1']).a == [1]


def test_deep_generic_with_referenced_generic():
    T = TypeVar('T')
    R = TypeVar('R')

    class ReferencedModel(GenericModel, Generic[R]):
        a: R

    class OuterModel(GenericModel, Generic[T]):
        a: ReferencedModel[T]

    class InnerModel(OuterModel[T], Generic[T]):
        pass

    assert InnerModel[int].__concrete__ is True
    assert InnerModel.__concrete__ is False

    with pytest.raises(ValidationError):
        InnerModel[int](a={'a': 'wrong'})
    assert InnerModel[int](a={'a': 1}).a.a == 1


def test_deep_generic_with_referenced_inner_generic():
    T = TypeVar('T')

    class ReferencedModel(GenericModel, Generic[T]):
        a: T

    class OuterModel(GenericModel, Generic[T]):
        a: Optional[List[Union[ReferencedModel[T], str]]]

    class InnerModel(OuterModel[T], Generic[T]):
        pass

    assert InnerModel[int].__concrete__ is True
    assert InnerModel.__concrete__ is False

    with pytest.raises(ValidationError):
        InnerModel[int](a=['s', {'a': 'wrong'}])
    assert InnerModel[int](a=['s', {'a': 1}]).a[1].a == 1

    assert InnerModel[int].__fields__['a'].outer_type_ == List[Union[ReferencedModel[int], str]]
    assert (InnerModel[int].__fields__['a'].sub_fields[0].sub_fields[0].outer_type_.__fields__['a'].outer_type_) == int


def test_deep_generic_with_multiple_typevars():
    T = TypeVar('T')
    U = TypeVar('U')

    class OuterModel(GenericModel, Generic[T]):
        data: List[T]

    class InnerModel(OuterModel[T], Generic[U, T]):
        extra: U

    ConcreteInnerModel = InnerModel[int, float]
    assert ConcreteInnerModel.__fields__['data'].outer_type_ == List[float]
    assert ConcreteInnerModel.__fields__['extra'].outer_type_ == int

    assert ConcreteInnerModel(data=['1'], extra='2').dict() == {'data': [1.0], 'extra': 2}


def test_deep_generic_with_multiple_inheritance():
    K = TypeVar('K')
    V = TypeVar('V')
    T = TypeVar('T')

    class OuterModelA(GenericModel, Generic[K, V]):
        data: Dict[K, V]

    class OuterModelB(GenericModel, Generic[T]):
        stuff: List[T]

    class InnerModel(OuterModelA[K, V], OuterModelB[T], Generic[K, V, T]):
        extra: int

    ConcreteInnerModel = InnerModel[int, float, str]

    assert ConcreteInnerModel.__fields__['data'].outer_type_ == Dict[int, float]
    assert ConcreteInnerModel.__fields__['stuff'].outer_type_ == List[str]
    assert ConcreteInnerModel.__fields__['extra'].outer_type_ == int

    ConcreteInnerModel(data={1.1: '5'}, stuff=[123], extra=5).dict() == {
        'data': {1: 5},
        'stuff': ['123'],
        'extra': 5,
    }


def test_generic_with_referenced_generic_type_1():
    T = TypeVar('T')

    class ModelWithType(GenericModel, Generic[T]):
        # Type resolves to type origin of "type" which is non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Type[T]

    class ReferenceModel(GenericModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    ReferenceModel[int]


def test_generic_with_referenced_nested_typevar():
    T = TypeVar('T')

    class ModelWithType(GenericModel, Generic[T]):
        # Type resolves to type origin of "collections.abc.Sequence" which is
        # non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Sequence[T]

    class ReferenceModel(GenericModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    ReferenceModel[int]


def test_generic_with_callable():
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        # Callable is a test for any type that accepts a list as an argument
        some_callable: Callable[[Optional[int], T], None]

    Model[str].__concrete__ is True
    Model.__concrete__ is False


def test_generic_with_partial_callable():
    T = TypeVar('T')
    U = TypeVar('U')

    class Model(GenericModel, Generic[T, U]):
        t: T
        u: U
        # Callable is a test for any type that accepts a list as an argument
        some_callable: Callable[[Optional[int], str], None]

    Model[str, U].__concrete__ is False
    Model[str, U].__parameters__ == [U]
    Model[str, int].__concrete__ is False


def test_generic_recursive_models(create_module):
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic.generics import GenericModel

        T = TypeVar('T')

        class Model1(GenericModel, Generic[T]):
            ref: 'Model2[T]'

        class Model2(GenericModel, Generic[T]):
            ref: Union[T, Model1[T]]

        Model1.update_forward_refs()

    Model1 = module.Model1
    Model2 = module.Model2
    result = Model1[str].parse_obj(dict(ref=dict(ref=dict(ref=dict(ref=123)))))
    assert result == Model1(ref=Model2(ref=Model1(ref=Model2(ref='123'))))


def test_generic_enum():
    T = TypeVar('T')

    class SomeGenericModel(GenericModel, Generic[T]):
        some_field: T

    class SomeStringEnum(str, Enum):
        A = 'A'
        B = 'B'

    class MyModel(BaseModel):
        my_gen: SomeGenericModel[SomeStringEnum]

    m = MyModel.parse_obj({'my_gen': {'some_field': 'A'}})
    assert m.my_gen.some_field is SomeStringEnum.A


def test_generic_literal():
    FieldType = TypeVar('FieldType')
    ValueType = TypeVar('ValueType')

    class GModel(GenericModel, Generic[FieldType, ValueType]):
        field: Dict[FieldType, ValueType]

    Fields = Literal['foo', 'bar']
    m = GModel[Fields, str](field={'foo': 'x'})
    assert m.dict() == {'field': {'foo': 'x'}}


def test_generic_enums():
    T = TypeVar('T')

    class GModel(GenericModel, Generic[T]):
        x: T

    class EnumA(str, Enum):
        a = 'a'

    class EnumB(str, Enum):
        b = 'b'

    class Model(BaseModel):
        g_a: GModel[EnumA]
        g_b: GModel[EnumB]

    assert set(Model.schema()['definitions']) == {'EnumA', 'EnumB', 'GModel_EnumA_', 'GModel_EnumB_'}


def test_generic_with_user_defined_generic_field():
    T = TypeVar('T')

    class GenericList(List[T]):
        pass

    class Model(GenericModel, Generic[T]):
        field: GenericList[T]

    model = Model[int](field=[5])
    assert model.field[0] == 5

    with pytest.raises(ValidationError):
        model = Model[int](field=['a'])


def test_generic_annotated():
    T = TypeVar('T')

    class SomeGenericModel(GenericModel, Generic[T]):
        some_field: Annotated[T, Field(alias='the_alias')]

    SomeGenericModel[str](the_alias='qwe')


def test_generic_subclass():
    T = TypeVar('T')

    class A(GenericModel, Generic[T]):
        ...

    class B(A[T], Generic[T]):
        ...

    assert B[int].__name__ == 'B[int]'
    assert issubclass(B[int], B)
    assert issubclass(B[int], A[int])
    assert not issubclass(B[int], A[str])


def test_generic_subclass_with_partial_application():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(GenericModel, Generic[T]):
        ...

    class B(A[S], Generic[T, S]):
        ...

    PartiallyAppliedB = B[str, T]
    assert issubclass(PartiallyAppliedB[int], A[int])
    assert not issubclass(PartiallyAppliedB[int], A[str])
    assert not issubclass(PartiallyAppliedB[str], A[int])


def test_multilevel_generic_binding():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(GenericModel, Generic[T, S]):
        ...

    class B(A[str, T], Generic[T]):
        ...

    assert B[int].__name__ == 'B[int]'
    assert issubclass(B[int], A[str, int])
    assert not issubclass(B[str], A[str, int])


def test_generic_subclass_with_extra_type():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(GenericModel, Generic[T]):
        ...

    class B(A[S], Generic[T, S]):
        ...

    assert B[int, str].__name__ == 'B[int, str]', B[int, str].__name__
    assert issubclass(B[str, int], B)
    assert issubclass(B[str, int], A[int])
    assert not issubclass(B[int, str], A[int])


def test_multi_inheritance_generic_binding():
    T = TypeVar('T')

    class A(GenericModel, Generic[T]):
        ...

    class B(A[int], Generic[T]):
        ...

    class C(B[str], Generic[T]):
        ...

    assert C[float].__name__ == 'C[float]'
    assert issubclass(C[float], B[str])
    assert not issubclass(C[float], B[int])
    assert issubclass(C[float], A[int])
    assert not issubclass(C[float], A[str])


def test_parse_generic_json():
    T = TypeVar('T')

    class MessageWrapper(GenericModel, Generic[T]):
        message: Json[T]

    class Payload(BaseModel):
        payload_field: str

    raw = json.dumps({'payload_field': 'payload'})
    record = MessageWrapper[Payload](message=raw)
    assert isinstance(record.message, Payload)

    schema = record.schema()
    assert schema['properties'] == {'message': {'$ref': '#/definitions/Payload'}}
    assert schema['definitions']['Payload'] == {
        'title': 'Payload',
        'type': 'object',
        'properties': {'payload_field': {'title': 'Payload Field', 'type': 'string'}},
        'required': ['payload_field'],
    }


def memray_limit_memory(limit):
    if '--memray' in sys.argv:
        return pytest.mark.limit_memory(limit)
    else:
        return pytest.mark.skip(reason='memray not enabled')


@memray_limit_memory('100 MB')
def test_generics_memory_use():
    """See:
    - https://github.com/pydantic/pydantic/issues/3829
    - https://github.com/pydantic/pydantic/pull/4083
    - https://github.com/pydantic/pydantic/pull/5052
    """

    T = TypeVar('T')
    U = TypeVar('U')
    V = TypeVar('V')

    class MyModel(GenericModel, Generic[T, U, V]):
        message: Json[T]
        field: Dict[U, V]

    class Outer(GenericModel, Generic[T]):
        inner: T

    types = [
        int,
        str,
        float,
        bool,
        bytes,
    ]

    containers = [
        List,
        Tuple,
        Set,
        FrozenSet,
    ]

    all = [*types, *[container[tp] for container in containers for tp in types]]

    total = list(itertools.product(all, all, all))

    for t1, t2, t3 in total:

        class Foo(MyModel[t1, t2, t3]):
            pass

        class _(Outer[Foo]):
            pass
