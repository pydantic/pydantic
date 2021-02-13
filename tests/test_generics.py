import sys
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union

import pytest

from pydantic import BaseModel, Field, ValidationError, root_validator, validator
from pydantic.generics import GenericModel, _generic_types_cache, iter_contained_typevars, replace_types

skip_36 = pytest.mark.skipif(sys.version_info < (3, 7), reason='generics only supported for python 3.7 and above')


@skip_36
def test_generic_name():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    if sys.version_info >= (3, 9):
        assert Result[list[int]].__name__ == 'Result[list[int]]'
    assert Result[List[int]].__name__ == 'Result[List[int]]'
    assert Result[int].__name__ == 'Result[int]'


@skip_36
def test_double_parameterize_error():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    with pytest.raises(TypeError) as exc_info:
        Result[int][int]

    assert str(exc_info.value) == 'Cannot parameterize a concrete instantiation of a generic model'


@skip_36
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


@skip_36
def test_methods_are_inherited():
    class CustomGenericModel(GenericModel):
        def method(self):
            return self.data

    T = TypeVar('T')

    class Model(CustomGenericModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    assert instance.method() == 1


@skip_36
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


@skip_36
def test_default_argument():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T
        other: bool = True

    result = Result[int](data=1)
    assert result.other is True


@skip_36
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


@skip_36
def test_classvar():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T
        other: ClassVar[int] = 1

    assert Result.other == 1
    assert Result[int].other == 1
    assert Result[int](data=1).other == 1
    assert 'other' not in Result.__fields__


@skip_36
def test_non_annotated_field():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        data: T
        other = True

    assert 'other' in Result.__fields__
    assert 'other' in Result[int].__fields__

    result = Result[int](data=1)
    assert result.other is True


@skip_36
def test_must_inherit_from_generic():
    with pytest.raises(TypeError) as exc_info:

        class Result(GenericModel):
            pass

        Result[int]

    assert str(exc_info.value) == 'Type Result must inherit from typing.Generic before being parameterized'


@skip_36
def test_parameters_placed_on_generic():
    T = TypeVar('T')
    with pytest.raises(TypeError, match='Type parameters should be placed on typing.Generic, not GenericModel'):

        class Result(GenericModel[T]):
            pass


@skip_36
def test_parameters_must_be_typevar():
    with pytest.raises(TypeError, match='Type GenericModel must inherit from typing.Generic before being '):

        class Result(GenericModel[int]):
            pass


@skip_36
def test_subclass_can_be_genericized():
    T = TypeVar('T')

    class Result(GenericModel, Generic[T]):
        pass

    Result[T]


@skip_36
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


@skip_36
def test_cover_cache():
    cache_size = len(_generic_types_cache)
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        x: T

    Model[int]  # adds both with-tuple and without-tuple version to cache
    assert len(_generic_types_cache) == cache_size + 2
    Model[int]  # uses the cache
    assert len(_generic_types_cache) == cache_size + 2


@skip_36
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


@skip_36
def test_enum_generic():
    T = TypeVar('T')

    class MyEnum(Enum):
        x = 1
        y = 2

    class Model(GenericModel, Generic[T]):
        enum: T

    Model[MyEnum](enum=MyEnum.x)
    Model[MyEnum](enum=2)


@skip_36
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


@skip_36
def test_alongside_concrete_generics():
    from pydantic.generics import GenericModel

    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        item: T
        metadata: Dict[str, Any]

    model = MyModel[int](item=1, metadata={})
    assert model.item == 1
    assert model.metadata == {}


@skip_36
def test_complex_nesting():
    from pydantic.generics import GenericModel

    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        item: List[Dict[Union[int, T], str]]

    item = [{1: 'a', 'a': 'a'}]
    model = MyModel[str](item=item)
    assert model.item == item


@skip_36
def test_required_value():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        MyModel[int]()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


@skip_36
def test_optional_value():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        a: Optional[int] = 1

    model = MyModel[int]()
    assert model.dict() == {'a': 1}


@skip_36
def test_custom_schema():
    T = TypeVar('T')

    class MyModel(GenericModel, Generic[T]):
        a: int = Field(1, description='Custom')

    schema = MyModel[int].schema()
    assert schema['properties']['a'].get('description') == 'Custom'


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
def test_iter_contained_typevars():
    T = TypeVar('T')
    T2 = TypeVar('T2')

    class Model(GenericModel, Generic[T]):
        a: T

    assert list(iter_contained_typevars(Model[T])) == [T]
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[T]]]])) == [T]
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[int]]]])) == []
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[T], Callable[[T2, T], str]]]])) == [T, T2, T]


@skip_36
def test_nested_identity_parameterization():
    T = TypeVar('T')
    T2 = TypeVar('T2')

    class Model(GenericModel, Generic[T]):
        a: T

    assert Model[T][T][T] is Model
    assert Model[T] is Model
    assert Model[T2] is not Model


@skip_36
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


@skip_36
def test_replace_types_identity_on_unchanged():
    T = TypeVar('T')
    U = TypeVar('U')

    type_ = List[Union[str, Callable[[list], Optional[str]], U]]
    assert replace_types(type_, {T: int}) is type_


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
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


@skip_36
def test_generic_with_referenced_generic_type_1():
    T = TypeVar('T')

    class ModelWithType(GenericModel, Generic[T]):
        # Type resolves to type origin of "type" which is non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Type[T]

    class ReferenceModel(GenericModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    ReferenceModel[int]


@skip_36
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


@skip_36
def test_generic_with_callable():
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        # Callable is a test for any type that accepts a list as an argument
        some_callable: Callable[[Optional[int], T], None]

    Model[str].__concrete__ is True
    Model.__concrete__ is False


@skip_36
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
