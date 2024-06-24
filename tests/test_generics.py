import gc
import itertools
import json
import platform
import re
import sys
from collections import deque
from enum import Enum, IntEnum
from typing import (
    Any,
    Callable,
    ClassVar,
    Counter,
    DefaultDict,
    Deque,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    OrderedDict,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pytest
from dirty_equals import HasRepr, IsStr
from pydantic_core import CoreSchema, core_schema
from typing_extensions import (
    Annotated,
    Literal,
    NotRequired,
    ParamSpec,
    TypedDict,
    TypeVarTuple,
    Unpack,
    get_args,
)
from typing_extensions import (
    TypeVar as TypingExtensionsTypeVar,
)

from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    Json,
    PositiveInt,
    PydanticSchemaGenerationError,
    PydanticUserError,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic._internal._core_utils import collect_invalid_schemas
from pydantic._internal._generics import (
    _GENERIC_TYPES_CACHE,
    _LIMITED_DICT_SIZE,
    LimitedDict,
    generic_recursion_self_type,
    iter_contained_typevars,
    recursively_defined_type_refs,
    replace_types,
)
from pydantic.warnings import GenericBeforeBaseModelWarning


@pytest.fixture()
def clean_cache():
    # cleans up _GENERIC_TYPES_CACHE for checking item counts in the cache
    _GENERIC_TYPES_CACHE.clear()
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)


def test_generic_name():
    data_type = TypeVar('data_type')

    class Result(BaseModel, Generic[data_type]):
        data: data_type

    if sys.version_info >= (3, 9):
        assert Result[list[int]].__name__ == 'Result[list[int]]'
    assert Result[List[int]].__name__ == 'Result[List[int]]'
    assert Result[int].__name__ == 'Result[int]'


def test_double_parameterize_error():
    data_type = TypeVar('data_type')

    class Result(BaseModel, Generic[data_type]):
        data: data_type

    with pytest.raises(TypeError) as exc_info:
        Result[int][int]

    assert str(exc_info.value) == "<class 'tests.test_generics.Result[int]'> is not a generic class"


def test_value_validation():
    T = TypeVar('T', bound=Dict[Any, Any])

    class Response(BaseModel, Generic[T]):
        data: T

        @field_validator('data')
        @classmethod
        def validate_value_nonzero(cls, v: Any):
            if any(x == 0 for x in v.values()):
                raise ValueError('some value is zero')
            return v

        @model_validator(mode='after')
        def validate_sum(self) -> 'Response[T]':
            data = self.data
            if sum(data.values()) > 5:
                raise ValueError('sum too large')
            return self

    assert Response[Dict[int, int]](data={1: '4'}).model_dump() == {'data': {1: 4}}
    with pytest.raises(ValidationError) as exc_info:
        Response[Dict[int, int]](data={1: 'a'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('data', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Response[Dict[int, int]](data={1: 0})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'error': HasRepr(repr(ValueError('some value is zero')))},
            'input': {1: 0},
            'loc': ('data',),
            'msg': 'Value error, some value is zero',
            'type': 'value_error',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Response[Dict[int, int]](data={1: 3, 2: 6})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'error': HasRepr(repr(ValueError('sum too large')))},
            'input': {'data': {1: 3, 2: 6}},
            'loc': (),
            'msg': 'Value error, sum too large',
            'type': 'value_error',
        }
    ]


def test_methods_are_inherited():
    class CustomModel(BaseModel):
        def method(self):
            return self.data

    T = TypeVar('T')

    class Model(CustomModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    assert instance.method() == 1


def test_config_is_inherited():
    class CustomGenericModel(BaseModel, frozen=True): ...

    T = TypeVar('T')

    class Model(CustomGenericModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    with pytest.raises(ValidationError) as exc_info:
        instance.data = 2
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_instance', 'loc': ('data',), 'msg': 'Instance is frozen', 'input': 2}
    ]


def test_default_argument():
    T = TypeVar('T')

    class Result(BaseModel, Generic[T]):
        data: T
        other: bool = True

    result = Result[int](data=1)
    assert result.other is True


def test_default_argument_for_typevar():
    T = TypeVar('T')

    class Result(BaseModel, Generic[T]):
        data: T = 4

    result = Result[int]()
    assert result.data == 4

    result = Result[float]()
    assert result.data == 4

    result = Result[int](data=1)
    assert result.data == 1


def test_classvar():
    T = TypeVar('T')

    class Result(BaseModel, Generic[T]):
        data: T
        other: ClassVar[int] = 1

    assert Result.other == 1
    assert Result[int].other == 1
    assert Result[int](data=1).other == 1
    assert 'other' not in Result.model_fields


def test_non_annotated_field():
    T = TypeVar('T')

    with pytest.raises(PydanticUserError, match='A non-annotated attribute was detected: `other = True`'):

        class Result(BaseModel, Generic[T]):
            data: T
            other = True


def test_non_generic_field():
    T = TypeVar('T')

    class Result(BaseModel, Generic[T]):
        data: T
        other: bool = True

    assert 'other' in Result.model_fields
    assert 'other' in Result[int].model_fields

    result = Result[int](data=1)
    assert result.other is True


def test_must_inherit_from_generic():
    with pytest.raises(TypeError) as exc_info:

        class Result(BaseModel):
            pass

        Result[int]

    assert str(exc_info.value) == (
        "<class 'tests.test_generics.test_must_inherit_from_generic.<locals>.Result'> cannot be "
        'parametrized because it does not inherit from typing.Generic'
    )


def test_parameters_placed_on_generic():
    T = TypeVar('T')
    with pytest.raises(TypeError, match='Type parameters should be placed on typing.Generic, not BaseModel'):

        class Result(BaseModel[T]):
            pass


def test_parameters_must_be_typevar():
    with pytest.raises(TypeError, match='Type parameters should be placed on typing.Generic, not BaseModel'):

        class Result(BaseModel[int]):
            pass


def test_subclass_can_be_genericized():
    T = TypeVar('T')

    class Result(BaseModel, Generic[T]):
        pass

    Result[T]


def test_parameter_count():
    T = TypeVar('T')
    S = TypeVar('S')

    class Model(BaseModel, Generic[T, S]):
        x: T
        y: S

    with pytest.raises(TypeError) as exc_info:
        Model[int, int, int]

    # This error message, which comes from `typing`, changed 'parameters' to 'arguments' in 3.11
    error_message = str(exc_info.value)
    assert error_message.startswith('Too many parameters') or error_message.startswith('Too many arguments')
    assert error_message.endswith(
        " for <class 'tests.test_generics.test_parameter_count.<locals>.Model'>; actual 3, expected 2"
    )


def test_cover_cache(clean_cache):
    cache_size = len(_GENERIC_TYPES_CACHE)
    T = TypeVar('T')

    class Model(BaseModel, Generic[T]):
        x: T

    models = []  # keep references to models to get cache size

    models.append(Model[int])  # adds both with-tuple and without-tuple version to cache
    assert len(_GENERIC_TYPES_CACHE) == cache_size + 3
    models.append(Model[int])  # uses the cache
    assert len(_GENERIC_TYPES_CACHE) == cache_size + 3
    del models


def test_cache_keys_are_hashable(clean_cache):
    cache_size = len(_GENERIC_TYPES_CACHE)
    T = TypeVar('T')
    C = Callable[[str, Dict[str, Any]], Iterable[str]]

    class MyGenericModel(BaseModel, Generic[T]):
        t: T

    # Callable's first params get converted to a list, which is not hashable.
    # Make sure we can handle that special case
    Simple = MyGenericModel[Callable[[int], str]]
    models = []  # keep references to models to get cache size
    models.append(Simple)

    assert len(_GENERIC_TYPES_CACHE) == cache_size + 3
    # Nested Callables
    models.append(MyGenericModel[Callable[[C], Iterable[str]]])
    assert len(_GENERIC_TYPES_CACHE) == cache_size + 6
    models.append(MyGenericModel[Callable[[Simple], Iterable[int]]])
    assert len(_GENERIC_TYPES_CACHE) == cache_size + 9
    models.append(MyGenericModel[Callable[[MyGenericModel[C]], Iterable[int]]])
    assert len(_GENERIC_TYPES_CACHE) == cache_size + 15

    class Model(BaseModel):
        x: MyGenericModel[Callable[[C], Iterable[str]]] = Field(...)

    models.append(Model)
    assert len(_GENERIC_TYPES_CACHE) == cache_size + 15
    del models


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='PyPy does not play nice with PyO3 gc')
def test_caches_get_cleaned_up(clean_cache):
    initial_types_cache_size = len(_GENERIC_TYPES_CACHE)
    T = TypeVar('T')

    class MyGenericModel(BaseModel, Generic[T]):
        x: T

        model_config = dict(arbitrary_types_allowed=True)

    n_types = 200
    types = []
    for i in range(n_types):

        class MyType(int):
            pass

        types.append(MyGenericModel[MyType])  # retain a reference

    assert len(_GENERIC_TYPES_CACHE) == initial_types_cache_size + 3 * n_types
    types.clear()
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    assert len(_GENERIC_TYPES_CACHE) < initial_types_cache_size + _LIMITED_DICT_SIZE


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='PyPy does not play nice with PyO3 gc')
def test_caches_get_cleaned_up_with_aliased_parametrized_bases(clean_cache):
    types_cache_size = len(_GENERIC_TYPES_CACHE)

    def run() -> None:  # Run inside nested function to get classes in local vars cleaned also
        T1 = TypeVar('T1')
        T2 = TypeVar('T2')

        class A(BaseModel, Generic[T1, T2]):
            x: T1
            y: T2

        B = A[int, T2]
        C = B[str]
        assert len(_GENERIC_TYPES_CACHE) == types_cache_size + 5
        del C
        del B
        gc.collect()

    run()

    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    assert len(_GENERIC_TYPES_CACHE) < types_cache_size + _LIMITED_DICT_SIZE


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='PyPy does not play nice with PyO3 gc')
@pytest.mark.skipif(sys.version_info[:2] == (3, 9), reason='The test randomly fails on Python 3.9')
def test_circular_generic_refs_get_cleaned_up():
    initial_cache_size = len(_GENERIC_TYPES_CACHE)

    def fn():
        T = TypeVar('T')
        C = TypeVar('C')

        class Inner(BaseModel, Generic[T, C]):
            a: T
            b: C

        class Outer(BaseModel, Generic[C]):
            c: Inner[int, C]

        klass = Outer[str]
        assert len(_GENERIC_TYPES_CACHE) > initial_cache_size
        assert klass in _GENERIC_TYPES_CACHE.values()

    fn()

    gc.collect(0)
    gc.collect(1)
    gc.collect(2)

    assert len(_GENERIC_TYPES_CACHE) == initial_cache_size


def test_generics_work_with_many_parametrized_base_models(clean_cache):
    cache_size = len(_GENERIC_TYPES_CACHE)
    count_create_models = 1000
    T = TypeVar('T')
    C = TypeVar('C')

    class A(BaseModel, Generic[T, C]):
        x: T
        y: C

    class B(A[int, C], BaseModel, Generic[C]):
        pass

    models = []
    for i in range(count_create_models):

        class M(BaseModel):
            pass

        M.__name__ = f'M{i}'
        models.append(M)

    generics = []
    for m in models:
        Working = B[m]
        generics.append(Working)

    target_size = cache_size + count_create_models * 3 + 2
    assert len(_GENERIC_TYPES_CACHE) < target_size + _LIMITED_DICT_SIZE
    del models
    del generics


def test_generic_config():
    data_type = TypeVar('data_type')

    class Result(BaseModel, Generic[data_type], frozen=True):
        data: data_type

    result = Result[int](data=1)
    assert result.data == 1
    with pytest.raises(ValidationError):
        result.data = 2


def test_enum_generic():
    T = TypeVar('T')

    class MyEnum(IntEnum):
        x = 1
        y = 2

    class Model(BaseModel, Generic[T]):
        enum: T

    Model[MyEnum](enum=MyEnum.x)
    Model[MyEnum](enum=2)


def test_generic():
    data_type = TypeVar('data_type')
    error_type = TypeVar('error_type')

    class Result(BaseModel, Generic[data_type, error_type]):
        data: Optional[List[data_type]] = None
        error: Optional[error_type] = None
        positive_number: int

        @field_validator('error')
        @classmethod
        def validate_error(cls, v: Optional[error_type], info: ValidationInfo) -> Optional[error_type]:
            values = info.data
            if values.get('data', None) is None and v is None:
                raise ValueError('Must provide data or error')
            if values.get('data', None) is not None and v is not None:
                raise ValueError('Must not provide both data and error')
            return v

        @field_validator('positive_number')
        @classmethod
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
    assert success1.model_dump() == {'data': [{'number': 1, 'text': 'a'}], 'error': None, 'positive_number': 1}
    assert repr(success1) == (
        'Result[test_generic.<locals>.Data,'
        " test_generic.<locals>.Error](data=[Data(number=1, text='a')], error=None, positive_number=1)"
    )

    success2 = Result[Data, Error](error=Error(message='error'), positive_number=1)
    assert success2.model_dump() == {'data': None, 'error': {'message': 'error'}, 'positive_number': 1}
    assert repr(success2) == (
        'Result[test_generic.<locals>.Data, test_generic.<locals>.Error]'
        "(data=None, error=Error(message='error'), positive_number=1)"
    )
    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](error=Error(message='error'), positive_number=-1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'error': HasRepr(repr(ValueError()))},
            'input': -1,
            'loc': ('positive_number',),
            'msg': 'Value error, ',
            'type': 'value_error',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text='a')], error=Error(message='error'), positive_number=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'error': HasRepr(repr(ValueError('Must not provide both data and error')))},
            'input': Error(message='error'),
            'loc': ('error',),
            'msg': 'Value error, Must not provide both data and error',
            'type': 'value_error',
        }
    ]


def test_alongside_concrete_generics():
    T = TypeVar('T')

    class MyModel(BaseModel, Generic[T]):
        item: T
        metadata: Dict[str, Any]

    model = MyModel[int](item=1, metadata={})
    assert model.item == 1
    assert model.metadata == {}


def test_complex_nesting():
    T = TypeVar('T')

    class MyModel(BaseModel, Generic[T]):
        item: List[Dict[Union[int, T], str]]

    item = [{1: 'a', 'a': 'a'}]
    model = MyModel[str](item=item)
    assert model.item == item


def test_required_value():
    T = TypeVar('T')

    class MyModel(BaseModel, Generic[T]):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        MyModel[int]()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_optional_value():
    T = TypeVar('T')

    class MyModel(BaseModel, Generic[T]):
        a: Optional[int] = 1

    model = MyModel[int]()
    assert model.model_dump() == {'a': 1}


def test_custom_schema():
    T = TypeVar('T')

    class MyModel(BaseModel, Generic[T]):
        a: int = Field(1, description='Custom')

    schema = MyModel[int].model_json_schema()
    assert schema['properties']['a'].get('description') == 'Custom'


def test_child_schema():
    T = TypeVar('T')

    class Model(BaseModel, Generic[T]):
        a: T

    class Child(Model[T], Generic[T]):
        pass

    schema = Child[int].model_json_schema()
    assert schema == {
        'title': 'Child[int]',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
    }


def test_custom_generic_naming():
    T = TypeVar('T')

    class MyModel(BaseModel, Generic[T]):
        value: Optional[T]

        @classmethod
        def model_parametrized_name(cls, params: Tuple[Type[Any], ...]) -> str:
            param_names = [param.__name__ if hasattr(param, '__name__') else str(param) for param in params]
            title = param_names[0].title()
            return f'Optional{title}Wrapper'

    assert repr(MyModel[int](value=1)) == 'OptionalIntWrapper(value=1)'
    assert repr(MyModel[str](value=None)) == 'OptionalStrWrapper(value=None)'


def test_nested():
    AT = TypeVar('AT')

    class InnerT(BaseModel, Generic[AT]):
        a: AT

    inner_int = InnerT[int](a=8)
    inner_str = InnerT[str](a='ate')
    inner_dict_any = InnerT[Any](a={})
    inner_int_any = InnerT[Any](a=7)

    class OuterT_SameType(BaseModel, Generic[AT]):
        i: InnerT[AT]

    OuterT_SameType[int](i={'a': 8})
    OuterT_SameType[int](i=inner_int)
    OuterT_SameType[str](i=inner_str)
    # TODO: The next line is failing, but passes in v1.
    #   Should re-parse-from-dict if the pydantic_generic_origin is the same
    # OuterT_SameType[str](i=inner_int_any)
    OuterT_SameType[int](i=inner_int_any.model_dump())

    with pytest.raises(ValidationError) as exc_info:
        OuterT_SameType[int](i=inner_str.model_dump())
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('i', 'a'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'ate',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        OuterT_SameType[int](i=inner_str)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('i',),
            'msg': 'Input should be a valid dictionary or instance of InnerT[int]',
            'input': InnerT[str](a='ate'),
            'ctx': {'class_name': 'InnerT[int]'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        OuterT_SameType[int](i=inner_dict_any.model_dump())
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('i', 'a'), 'msg': 'Input should be a valid integer', 'input': {}}
    ]

    with pytest.raises(ValidationError) as exc_info:
        OuterT_SameType[int](i=inner_dict_any)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('i',),
            'msg': 'Input should be a valid dictionary or instance of InnerT[int]',
            'input': InnerT[Any](a={}),
            'ctx': {'class_name': 'InnerT[int]'},
        }
    ]


def test_partial_specification():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(BaseModel, Generic[AT, BT]):
        a: AT
        b: BT

    partial_model = Model[int, BT]
    concrete_model = partial_model[str]
    concrete_model(a=1, b='abc')
    with pytest.raises(ValidationError) as exc_info:
        concrete_model(a='abc', b=None)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'abc',
        },
        {'type': 'string_type', 'loc': ('b',), 'msg': 'Input should be a valid string', 'input': None},
    ]


def test_partial_specification_with_inner_typevar():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(BaseModel, Generic[AT, BT]):
        a: List[AT]
        b: List[BT]

    partial_model = Model[int, BT]
    assert partial_model.__pydantic_generic_metadata__['parameters']
    concrete_model = partial_model[int]

    assert not concrete_model.__pydantic_generic_metadata__['parameters']

    # nested resolution of partial models should work as expected
    nested_resolved = concrete_model(a=['123'], b=['456'])
    assert nested_resolved.a == [123]
    assert nested_resolved.b == [456]


@pytest.mark.skipif(sys.version_info < (3, 12), reason='repr different on older versions')
def test_partial_specification_name():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(BaseModel, Generic[AT, BT]):
        a: AT
        b: BT

    partial_model = Model[int, BT]
    assert partial_model.__name__ == 'Model[int, TypeVar]'
    concrete_model = partial_model[str]
    assert concrete_model.__name__ == 'Model[int, str]'


def test_partial_specification_instantiation():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(BaseModel, Generic[AT, BT]):
        a: AT
        b: BT

    partial_model = Model[int, BT]
    partial_model(a=1, b=2)

    partial_model(a=1, b='a')

    with pytest.raises(ValidationError) as exc_info:
        partial_model(a='a', b=2)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]


def test_partial_specification_instantiation_bounded():
    AT = TypeVar('AT')
    BT = TypeVar('BT', bound=int)

    class Model(BaseModel, Generic[AT, BT]):
        a: AT
        b: BT

    Model(a=1, b=1)
    with pytest.raises(ValidationError) as exc_info:
        Model(a=1, b='a')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]

    partial_model = Model[int, BT]
    partial_model(a=1, b=1)
    with pytest.raises(ValidationError) as exc_info:
        partial_model(a=1, b='a')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]


def test_typevar_parametrization():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(BaseModel, Generic[AT, BT]):
        a: AT
        b: BT

    CT = TypeVar('CT', bound=int)
    DT = TypeVar('DT', bound=int)

    with pytest.raises(ValidationError) as exc_info:
        Model[CT, DT](a='a', b='b')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
    ]


def test_multiple_specification():
    AT = TypeVar('AT')
    BT = TypeVar('BT')

    class Model(BaseModel, Generic[AT, BT]):
        a: AT
        b: BT

    CT = TypeVar('CT')
    partial_model = Model[CT, CT]
    concrete_model = partial_model[str]

    with pytest.raises(ValidationError) as exc_info:
        concrete_model(a=None, b=None)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('a',), 'msg': 'Input should be a valid string', 'input': None},
        {'type': 'string_type', 'loc': ('b',), 'msg': 'Input should be a valid string', 'input': None},
    ]


def test_generic_subclass_of_concrete_generic():
    T = TypeVar('T')
    U = TypeVar('U')

    class GenericBaseModel(BaseModel, Generic[T]):
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
    # objects with <locals> in their __qualname__  (e.g. defined in function)
    @create_module
    def module():
        import pickle
        from typing import Generic, TypeVar

        from pydantic import BaseModel

        t = TypeVar('t')

        class Model(BaseModel):
            a: float
            b: int = 10

        class MyGeneric(BaseModel, Generic[t]):
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

        t = TypeVar('t')

        class Model(BaseModel):
            a: float
            b: int = 10

        class MyGeneric(BaseModel, Generic[t]):
            value: t

        def get_generic(t):
            return MyGeneric[t]

        original = get_generic(Model)(value=Model(a='24'))
        with pytest.raises(pickle.PicklingError):
            pickle.dumps(original)


def test_generic_model_redefined_without_cache_fail(create_module, monkeypatch):
    # match identity checker otherwise we never get to the redefinition check
    monkeypatch.setattr('pydantic._internal._utils.all_identical', lambda left, right: False)

    @create_module
    def module():
        from typing import Generic, TypeVar

        from pydantic import BaseModel
        from pydantic._internal._generics import _GENERIC_TYPES_CACHE

        t = TypeVar('t')

        class MyGeneric(BaseModel, Generic[t]):
            value: t

        class Model(BaseModel): ...

        concrete = MyGeneric[Model]
        _GENERIC_TYPES_CACHE.clear()
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

        from pydantic import BaseModel

        t = TypeVar('t')

        class Model(BaseModel, Generic[t]):
            data: t

        int_or_float_model = Model[Union[int, float]]
        float_or_int_model = Model[Union[float, int]]

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

        from pydantic import BaseModel

        t = TypeVar('t')

        class Model(BaseModel, Generic[t]):
            data: t

        int_or_float_model = Model[List[Union[int, float]]]
        float_or_int_model = Model[List[Union[float, int]]]

        assert type(int_or_float_model(data=['1']).data[0]) is int
        assert type(float_or_int_model(data=['1']).data[0]) is float


def test_get_caller_frame_info(create_module):
    @create_module
    def module():
        from pydantic._internal._generics import _get_caller_frame_info

        def function():
            assert _get_caller_frame_info() == (__name__, True)

            another_function()

        def another_function():
            assert _get_caller_frame_info() == (__name__, False)
            third_function()

        def third_function():
            assert _get_caller_frame_info() == (__name__, False)

        function()


def test_get_caller_frame_info_called_from_module(create_module):
    @create_module
    def module():
        from unittest.mock import patch

        import pytest

        from pydantic._internal._generics import _get_caller_frame_info

        with pytest.raises(RuntimeError, match='This function must be used inside another function'):
            with patch('sys._getframe', side_effect=ValueError('getframe_exc')):
                _get_caller_frame_info()


def test_get_caller_frame_info_when_sys_getframe_undefined():
    from pydantic._internal._generics import _get_caller_frame_info

    getframe = sys._getframe
    del sys._getframe
    try:
        assert _get_caller_frame_info() == (None, False)
    finally:  # just to make sure we always setting original attribute back
        sys._getframe = getframe


def test_iter_contained_typevars():
    T = TypeVar('T')
    T2 = TypeVar('T2')

    class Model(BaseModel, Generic[T]):
        a: T

    assert list(iter_contained_typevars(Model[T])) == [T]
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[T]]]])) == [T]
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[int]]]])) == []
    assert list(iter_contained_typevars(Optional[List[Union[str, Model[T], Callable[[T2, T], str]]]])) == [T, T2, T]


def test_nested_identity_parameterization():
    T = TypeVar('T')
    T2 = TypeVar('T2')

    class Model(BaseModel, Generic[T]):
        a: T

    assert Model[T][T][T] is Model
    assert Model[T] is Model
    assert Model[T2] is not Model


def test_replace_types():
    T = TypeVar('T')

    class Model(BaseModel, Generic[T]):
        a: T

    assert replace_types(T, {T: int}) is int
    assert replace_types(List[Union[str, list, T]], {T: int}) == List[Union[str, list, int]]
    assert replace_types(Callable, {T: int}) == Callable
    assert replace_types(Callable[[int, str, T], T], {T: int}) == Callable[[int, str, int], int]
    assert replace_types(T, {}) is T
    assert replace_types(Model[List[T]], {T: int}) == Model[List[int]]
    assert replace_types(Model[List[T]], {T: int}) == Model[List[T]][int]
    assert (
        replace_types(Model[List[T]], {T: int}).model_fields['a'].annotation
        == Model[List[T]][int].model_fields['a'].annotation
    )
    assert replace_types(T, {}) is T
    assert replace_types(Type[T], {T: int}) == Type[int]
    assert replace_types(Model[T], {T: T}) == Model[T]
    assert replace_types(Json[T], {T: int}) == Json[int]

    if sys.version_info >= (3, 9):
        # Check generic aliases (subscripted builtin types) to make sure they
        # resolve correctly (don't get translated to typing versions for
        # example)
        assert replace_types(list[Union[str, list, T]], {T: int}) == list[Union[str, list, int]]

    if sys.version_info >= (3, 10):
        # Check that types.UnionType gets handled properly
        assert replace_types(str | list[T] | float, {T: int}) == str | list[int] | float


def test_replace_types_with_user_defined_generic_type_field():  # noqa: C901
    """Test that using user defined generic types as generic model fields are handled correctly."""
    T = TypeVar('T')
    KT = TypeVar('KT')
    VT = TypeVar('VT')

    class CustomCounter(Counter[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(Counter[get_args(source_type)[0]]))

    class CustomDefaultDict(DefaultDict[KT, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            keys_type, values_type = get_args(source_type)
            return core_schema.no_info_after_validator_function(
                lambda x: cls(x.default_factory, x), handler(DefaultDict[keys_type, values_type])
            )

    class CustomDeque(Deque[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(Deque[get_args(source_type)[0]]))

    class CustomDict(Dict[KT, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            keys_type, values_type = get_args(source_type)
            return core_schema.no_info_after_validator_function(cls, handler(Dict[keys_type, values_type]))

    class CustomFrozenset(FrozenSet[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(FrozenSet[get_args(source_type)[0]]))

    class CustomIterable(Iterable[T]):
        def __init__(self, iterable):
            self.iterable = iterable

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.iterable)

        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(Iterable[get_args(source_type)[0]]))

    class CustomList(List[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(List[get_args(source_type)[0]]))

    class CustomMapping(Mapping[KT, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            keys_type, values_type = get_args(source_type)
            return handler(Mapping[keys_type, values_type])

    class CustomOrderedDict(OrderedDict[KT, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            keys_type, values_type = get_args(source_type)
            return core_schema.no_info_after_validator_function(cls, handler(OrderedDict[keys_type, values_type]))

    class CustomSet(Set[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(Set[get_args(source_type)[0]]))

    class CustomTuple(Tuple[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(Tuple[get_args(source_type)[0]]))

    class CustomLongTuple(Tuple[T, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(cls, handler(Tuple[get_args(source_type)]))

    class Model(BaseModel, Generic[T, KT, VT]):
        counter_field: CustomCounter[T]
        default_dict_field: CustomDefaultDict[KT, VT]
        deque_field: CustomDeque[T]
        dict_field: CustomDict[KT, VT]
        frozenset_field: CustomFrozenset[T]
        iterable_field: CustomIterable[T]
        list_field: CustomList[T]
        mapping_field: CustomMapping[KT, VT]
        ordered_dict_field: CustomOrderedDict[KT, VT]
        set_field: CustomSet[T]
        tuple_field: CustomTuple[T]
        long_tuple_field: CustomLongTuple[T, VT]

    assert replace_types(Model, {T: bool, KT: str, VT: int}) == Model[bool, str, int]
    assert replace_types(Model[T, KT, VT], {T: bool, KT: str, VT: int}) == Model[bool, str, int]
    assert replace_types(Model[T, VT, KT], {T: bool, KT: str, VT: int}) == Model[T, VT, KT][bool, int, str]

    m = Model[bool, str, int](
        counter_field=Counter([True, False]),
        default_dict_field={'a': 1},
        deque_field=[True, False],
        dict_field={'a': 1},
        frozenset_field=frozenset([True, False]),
        iterable_field=[True, False],
        list_field=[True, False],
        mapping_field={'a': 2},
        ordered_dict_field=OrderedDict([('a', 1)]),
        set_field={True, False},
        tuple_field=(True,),
        long_tuple_field=(True, 42),
    )

    # The following assertions are just to document the current behavior, and should
    # be updated if/when we do a better job of respecting the exact annotated type
    assert type(m.counter_field) is CustomCounter
    # assert type(m.default_dict_field) is CustomDefaultDict
    assert type(m.deque_field) is CustomDeque
    assert type(m.dict_field) is CustomDict
    assert type(m.frozenset_field) is CustomFrozenset
    assert type(m.iterable_field) is CustomIterable
    assert type(m.list_field) is CustomList
    assert type(m.mapping_field) is dict  # this is determined in CustomMapping.__get_pydantic_core_schema__
    assert type(m.ordered_dict_field) is CustomOrderedDict
    assert type(m.set_field) is CustomSet
    assert type(m.tuple_field) is CustomTuple
    assert type(m.long_tuple_field) is CustomLongTuple

    assert m.model_dump() == {
        'counter_field': {False: 1, True: 1},
        'default_dict_field': {'a': 1},
        'deque_field': deque([True, False]),
        'dict_field': {'a': 1},
        'frozenset_field': frozenset({False, True}),
        'iterable_field': HasRepr(IsStr(regex=r'SerializationIterator\(index=0, iterator=.*CustomIterable.*')),
        'list_field': [True, False],
        'mapping_field': {'a': 2},
        'ordered_dict_field': {'a': 1},
        'set_field': {False, True},
        'tuple_field': (True,),
        'long_tuple_field': (True, 42),
    }


def test_custom_sequence_behavior():
    T = TypeVar('T')

    class CustomSequence(Sequence[T]):
        pass

    with pytest.raises(
        PydanticSchemaGenerationError,
        match=(
            r'Unable to generate pydantic-core schema for .*'
            ' Set `arbitrary_types_allowed=True` in the model_config to ignore this error'
            ' or implement `__get_pydantic_core_schema__` on your type to fully support it'
        ),
    ):

        class Model(BaseModel, Generic[T]):
            x: CustomSequence[T]


def test_replace_types_identity_on_unchanged():
    T = TypeVar('T')
    U = TypeVar('U')

    type_ = List[Union[str, Callable[[list], Optional[str]], U]]
    assert replace_types(type_, {T: int}) is type_


def test_deep_generic():
    T = TypeVar('T')
    S = TypeVar('S')
    R = TypeVar('R')

    class OuterModel(BaseModel, Generic[T, S, R]):
        a: Dict[R, Optional[List[T]]]
        b: Optional[Union[S, R]]
        c: R
        d: float

    class InnerModel(BaseModel, Generic[T, R]):
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

    assert InnerModel.__pydantic_generic_metadata__['parameters']  # i.e., InnerModel is not concrete
    assert not inner_model.__pydantic_generic_metadata__['parameters']  # i.e., inner_model is concrete


def test_deep_generic_with_inner_typevar():
    T = TypeVar('T')

    class OuterModel(BaseModel, Generic[T]):
        a: List[T]

    class InnerModel(OuterModel[T], Generic[T]):
        pass

    assert not InnerModel[int].__pydantic_generic_metadata__['parameters']  # i.e., InnerModel[int] is concrete
    assert InnerModel.__pydantic_generic_metadata__['parameters']  # i.e., InnerModel is not concrete

    with pytest.raises(ValidationError):
        InnerModel[int](a=['wrong'])
    assert InnerModel[int](a=['1']).a == [1]


def test_deep_generic_with_referenced_generic():
    T = TypeVar('T')
    R = TypeVar('R')

    class ReferencedModel(BaseModel, Generic[R]):
        a: R

    class OuterModel(BaseModel, Generic[T]):
        a: ReferencedModel[T]

    class InnerModel(OuterModel[T], Generic[T]):
        pass

    assert not InnerModel[int].__pydantic_generic_metadata__['parameters']
    assert InnerModel.__pydantic_generic_metadata__['parameters']

    with pytest.raises(ValidationError):
        InnerModel[int](a={'a': 'wrong'})
    assert InnerModel[int](a={'a': 1}).a.a == 1


def test_deep_generic_with_referenced_inner_generic():
    T = TypeVar('T')

    class ReferencedModel(BaseModel, Generic[T]):
        a: T

    class OuterModel(BaseModel, Generic[T]):
        a: Optional[List[Union[ReferencedModel[T], str]]]

    class InnerModel(OuterModel[T], Generic[T]):
        pass

    assert not InnerModel[int].__pydantic_generic_metadata__['parameters']
    assert InnerModel.__pydantic_generic_metadata__['parameters']

    with pytest.raises(ValidationError):
        InnerModel[int](a=['s', {'a': 'wrong'}])
    assert InnerModel[int](a=['s', {'a': 1}]).a[1].a == 1

    assert InnerModel[int].model_fields['a'].annotation == Optional[List[Union[ReferencedModel[int], str]]]


def test_deep_generic_with_multiple_typevars():
    T = TypeVar('T')
    U = TypeVar('U')

    class OuterModel(BaseModel, Generic[T]):
        data: List[T]

    class InnerModel(OuterModel[T], Generic[U, T]):
        extra: U

    ConcreteInnerModel = InnerModel[int, float]

    assert ConcreteInnerModel.model_fields['data'].annotation == List[float]
    assert ConcreteInnerModel.model_fields['extra'].annotation == int

    assert ConcreteInnerModel(data=['1'], extra='2').model_dump() == {'data': [1.0], 'extra': 2}


def test_deep_generic_with_multiple_inheritance():
    K = TypeVar('K')
    V = TypeVar('V')
    T = TypeVar('T')

    class OuterModelA(BaseModel, Generic[K, V]):
        data: Dict[K, V]

    class OuterModelB(BaseModel, Generic[T]):
        stuff: List[T]

    class InnerModel(OuterModelA[K, V], OuterModelB[T], Generic[K, V, T]):
        extra: int

    ConcreteInnerModel = InnerModel[int, float, str]

    assert ConcreteInnerModel.model_fields['data'].annotation == Dict[int, float]
    assert ConcreteInnerModel.model_fields['stuff'].annotation == List[str]
    assert ConcreteInnerModel.model_fields['extra'].annotation == int

    with pytest.raises(ValidationError) as exc_info:
        ConcreteInnerModel(data={1.1: '5'}, stuff=[123], extra=5)
    assert exc_info.value.errors(include_url=False) == [
        {'input': 123, 'loc': ('stuff', 0), 'msg': 'Input should be a valid string', 'type': 'string_type'},
        {
            'input': 1.1,
            'loc': ('data', '1.1', '[key]'),
            'msg': 'Input should be a valid integer, got a number with a fractional part',
            'type': 'int_from_float',
        },
    ]

    assert ConcreteInnerModel(data={1: 5}, stuff=['123'], extra=5).model_dump() == {
        'data': {1: 5},
        'stuff': ['123'],
        'extra': 5,
    }


def test_generic_with_referenced_generic_type_1():
    T = TypeVar('T')

    class ModelWithType(BaseModel, Generic[T]):
        # Type resolves to type origin of "type" which is non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Type[T]

    class ReferenceModel(BaseModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    ReferenceModel[int]


def test_generic_with_referenced_generic_type_bound():
    T = TypeVar('T', bound=int)

    class ModelWithType(BaseModel, Generic[T]):
        # Type resolves to type origin of "type" which is non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Type[T]

    class ReferenceModel(BaseModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    class MyInt(int): ...

    ReferenceModel[MyInt]


def test_generic_with_referenced_generic_union_type_bound():
    T = TypeVar('T', bound=Union[str, int])

    class ModelWithType(BaseModel, Generic[T]):
        some_type: Type[T]

    class MyInt(int): ...

    class MyStr(str): ...

    ModelWithType[MyInt]
    ModelWithType[MyStr]


def test_generic_with_referenced_generic_type_constraints():
    T = TypeVar('T', int, str)

    class ModelWithType(BaseModel, Generic[T]):
        # Type resolves to type origin of "type" which is non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Type[T]

    class ReferenceModel(BaseModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    ReferenceModel[int]


def test_generic_with_referenced_nested_typevar():
    T = TypeVar('T')

    class ModelWithType(BaseModel, Generic[T]):
        # Type resolves to type origin of "collections.abc.Sequence" which is
        # non-subscriptible for
        # python < 3.9 so we want to make sure it works for other versions
        some_type: Sequence[T]

    class ReferenceModel(BaseModel, Generic[T]):
        abstract_base_with_type: ModelWithType[T]

    ReferenceModel[int]


def test_generic_with_callable():
    T = TypeVar('T')

    class Model(BaseModel, Generic[T]):
        # Callable is a test for any type that accepts a list as an argument
        some_callable: Callable[[Optional[int], T], None]

    assert not Model[str].__pydantic_generic_metadata__['parameters']
    assert Model.__pydantic_generic_metadata__['parameters']


def test_generic_with_partial_callable():
    T = TypeVar('T')
    U = TypeVar('U')

    class Model(BaseModel, Generic[T, U]):
        t: T
        u: U
        # Callable is a test for any type that accepts a list as an argument
        some_callable: Callable[[Optional[int], str], None]

    assert Model[str, U].__pydantic_generic_metadata__['parameters'] == (U,)
    assert not Model[str, int].__pydantic_generic_metadata__['parameters']


def test_generic_recursive_models(create_module):
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic import BaseModel

        T = TypeVar('T')

        class Model1(BaseModel, Generic[T]):
            ref: 'Model2[T]'

        class Model2(BaseModel, Generic[T]):
            ref: Union[T, Model1[T]]

        Model1.model_rebuild()

    Model1 = module.Model1
    Model2 = module.Model2

    with pytest.raises(ValidationError) as exc_info:
        Model1[str].model_validate(dict(ref=dict(ref=dict(ref=dict(ref=123)))))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('ref', 'ref', 'str'),
            'msg': 'Input should be a valid string',
            'input': {'ref': {'ref': 123}},
        },
        {
            'type': 'string_type',
            'loc': ('ref', 'ref', 'Model1[str]', 'ref', 'ref', 'str'),
            'msg': 'Input should be a valid string',
            'input': 123,
        },
        {
            'type': 'model_type',
            'loc': ('ref', 'ref', 'Model1[str]', 'ref', 'ref', 'Model1[str]'),
            'msg': 'Input should be a valid dictionary or instance of Model1[str]',
            'input': 123,
            'ctx': {'class_name': 'Model1[str]'},
        },
    ]
    result = Model1(ref=Model2(ref=Model1(ref=Model2(ref='123'))))
    assert result.model_dump() == {'ref': {'ref': {'ref': {'ref': '123'}}}}

    result = Model1[str].model_validate(dict(ref=dict(ref=dict(ref=dict(ref='123')))))
    assert result.model_dump() == {'ref': {'ref': {'ref': {'ref': '123'}}}}


def test_generic_recursive_models_separate_parameters(create_module):
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic import BaseModel

        T = TypeVar('T')

        class Model1(BaseModel, Generic[T]):
            ref: 'Model2[T]'

        S = TypeVar('S')

        class Model2(BaseModel, Generic[S]):
            ref: Union[S, Model1[S]]

        Model1.model_rebuild()

    Model1 = module.Model1
    # Model2 = module.Model2

    with pytest.raises(ValidationError) as exc_info:
        Model1[str].model_validate(dict(ref=dict(ref=dict(ref=dict(ref=123)))))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('ref', 'ref', 'str'),
            'msg': 'Input should be a valid string',
            'input': {'ref': {'ref': 123}},
        },
        {
            'type': 'string_type',
            'loc': ('ref', 'ref', 'Model1[str]', 'ref', 'ref', 'str'),
            'msg': 'Input should be a valid string',
            'input': 123,
        },
        {
            'type': 'model_type',
            'loc': ('ref', 'ref', 'Model1[str]', 'ref', 'ref', 'Model1[str]'),
            'msg': 'Input should be a valid dictionary or instance of Model1[str]',
            'input': 123,
            'ctx': {'class_name': 'Model1[str]'},
        },
    ]
    # TODO: Unlike in the previous test, the following (commented) line currently produces this error:
    #   >       result = Model1(ref=Model2(ref=Model1(ref=Model2(ref='123'))))
    #   E       pydantic_core._pydantic_core.ValidationError: 1 validation error for Model2[~T]
    #   E       ref
    #   E         Input should be a valid dictionary [type=dict_type, input_value=Model2(ref='123'), input_type=Model2]
    #  The root of this problem is that Model2[T] ends up being a proper subclass of Model2 since T != S.
    #  I am sure we can solve this problem, just need to put a bit more effort in.
    #  While I don't think we should block merging this functionality on getting the next line to pass,
    #  I think we should come back and resolve this at some point.
    # result = Model1(ref=Model2(ref=Model1(ref=Model2(ref='123'))))
    # assert result.model_dump() == {'ref': {'ref': {'ref': {'ref': '123'}}}}

    result = Model1[str].model_validate(dict(ref=dict(ref=dict(ref=dict(ref='123')))))
    assert result.model_dump() == {'ref': {'ref': {'ref': {'ref': '123'}}}}


def test_generic_recursive_models_repeated_separate_parameters(create_module):
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic import BaseModel

        T = TypeVar('T')

        class Model1(BaseModel, Generic[T]):
            ref: 'Model2[T]'
            ref2: Union['Model2[T]', None] = None

        S = TypeVar('S')

        class Model2(BaseModel, Generic[S]):
            ref: Union[S, Model1[S]]
            ref2: Union[S, Model1[S], None] = None

        Model1.model_rebuild()

    Model1 = module.Model1
    # Model2 = module.Model2

    with pytest.raises(ValidationError) as exc_info:
        Model1[str].model_validate(dict(ref=dict(ref=dict(ref=dict(ref=123)))))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('ref', 'ref', 'str'),
            'msg': 'Input should be a valid string',
            'input': {'ref': {'ref': 123}},
        },
        {
            'type': 'string_type',
            'loc': ('ref', 'ref', 'Model1[str]', 'ref', 'ref', 'str'),
            'msg': 'Input should be a valid string',
            'input': 123,
        },
        {
            'type': 'model_type',
            'loc': ('ref', 'ref', 'Model1[str]', 'ref', 'ref', 'Model1[str]'),
            'msg': 'Input should be a valid dictionary or instance of Model1[str]',
            'input': 123,
            'ctx': {'class_name': 'Model1[str]'},
        },
    ]

    result = Model1[str].model_validate(dict(ref=dict(ref=dict(ref=dict(ref='123')))))
    assert result.model_dump() == {
        'ref': {'ref': {'ref': {'ref': '123', 'ref2': None}, 'ref2': None}, 'ref2': None},
        'ref2': None,
    }


def test_generic_recursive_models_triple(create_module):
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic import BaseModel

        T1 = TypeVar('T1')
        T2 = TypeVar('T2')
        T3 = TypeVar('T3')

        class A1(BaseModel, Generic[T1]):
            a1: 'A2[T1]'

        class A2(BaseModel, Generic[T2]):
            a2: 'A3[T2]'

        class A3(BaseModel, Generic[T3]):
            a3: Union['A1[T3]', T3]

        A1.model_rebuild()

    A1 = module.A1

    with pytest.raises(ValidationError) as exc_info:
        A1[str].model_validate({'a1': {'a2': {'a3': 1}}})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('a1', 'a2', 'a3', 'A1[str]'),
            'msg': 'Input should be a valid dictionary or instance of A1[str]',
            'input': 1,
            'ctx': {'class_name': 'A1[str]'},
        },
        {'type': 'string_type', 'loc': ('a1', 'a2', 'a3', 'str'), 'msg': 'Input should be a valid string', 'input': 1},
    ]

    A1[int].model_validate({'a1': {'a2': {'a3': 1}}})


def test_generic_recursive_models_with_a_concrete_parameter(create_module):
    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic import BaseModel

        V1 = TypeVar('V1')
        V2 = TypeVar('V2')
        V3 = TypeVar('V3')

        class M1(BaseModel, Generic[V1, V2]):
            a: V1
            m: 'M2[V2]'

        class M2(BaseModel, Generic[V3]):
            m: Union[M1[int, V3], V3]

        M1.model_rebuild()

    M1 = module.M1

    # assert M1.__pydantic_core_schema__ == {}
    assert collect_invalid_schemas(M1.__pydantic_core_schema__) is False


def test_generic_recursive_models_complicated(create_module):
    """
    Note: If we drop the use of LimitedDict and use WeakValueDictionary only, this test will fail if run by itself.
        This is due to weird behavior with the WeakValueDictionary used for caching.
        As part of the next batch of generics work, we should attempt to fix this if possible.
        In the meantime, if this causes issues, or the test otherwise starts failing, please make it xfail
        with strict=False
    """

    @create_module
    def module():
        from typing import Generic, TypeVar, Union

        from pydantic import BaseModel

        T1 = TypeVar('T1')
        T2 = TypeVar('T2')
        T3 = TypeVar('T3')

        class A1(BaseModel, Generic[T1]):
            a1: 'A2[T1]'

        class A2(BaseModel, Generic[T2]):
            a2: 'A3[T2]'

        class A3(BaseModel, Generic[T3]):
            a3: Union[A1[T3], T3]

        A1.model_rebuild()

        S1 = TypeVar('S1')
        S2 = TypeVar('S2')

        class B1(BaseModel, Generic[S1]):
            a1: 'B2[S1]'

        class B2(BaseModel, Generic[S2]):
            a2: 'B1[S2]'

        B1.model_rebuild()

        V1 = TypeVar('V1')
        V2 = TypeVar('V2')
        V3 = TypeVar('V3')

        class M1(BaseModel, Generic[V1, V2]):
            a: int
            b: B1[V2]
            m: 'M2[V1]'

        class M2(BaseModel, Generic[V3]):
            m: Union[M1[V3, int], V3]

        M1.model_rebuild()

    M1 = module.M1

    assert collect_invalid_schemas(M1.__pydantic_core_schema__) is False


def test_generic_recursive_models_in_container(create_module):
    @create_module
    def module():
        from typing import Generic, List, Optional, TypeVar

        from pydantic import BaseModel

        T = TypeVar('T')

        class MyGenericModel(BaseModel, Generic[T]):
            foobar: Optional[List['MyGenericModel[T]']]
            spam: T

    MyGenericModel = module.MyGenericModel
    instance = MyGenericModel[int](foobar=[{'foobar': [], 'spam': 1}], spam=1)
    assert type(instance.foobar[0]) == MyGenericModel[int]


def test_generic_enum():
    T = TypeVar('T')

    class SomeGenericModel(BaseModel, Generic[T]):
        some_field: T

    class SomeStringEnum(str, Enum):
        A = 'A'
        B = 'B'

    class MyModel(BaseModel):
        my_gen: SomeGenericModel[SomeStringEnum]

    m = MyModel.model_validate({'my_gen': {'some_field': 'A'}})
    assert m.my_gen.some_field is SomeStringEnum.A


def test_generic_literal():
    FieldType = TypeVar('FieldType')
    ValueType = TypeVar('ValueType')

    class GModel(BaseModel, Generic[FieldType, ValueType]):
        field: Dict[FieldType, ValueType]

    Fields = Literal['foo', 'bar']
    m = GModel[Fields, str](field={'foo': 'x'})
    assert m.model_dump() == {'field': {'foo': 'x'}}


def test_generic_enums():
    T = TypeVar('T')

    class GModel(BaseModel, Generic[T]):
        x: T

    class EnumA(str, Enum):
        a = 'a'

    class EnumB(str, Enum):
        b = 'b'

    class Model(BaseModel):
        g_a: GModel[EnumA]
        g_b: GModel[EnumB]

    assert set(Model.model_json_schema()['$defs']) == {'EnumA', 'EnumB', 'GModel_EnumA_', 'GModel_EnumB_'}


def test_generic_with_user_defined_generic_field():
    T = TypeVar('T')

    class GenericList(List[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(GenericList, handler(List[get_args(source_type)[0]]))

    class Model(BaseModel, Generic[T]):
        field: GenericList[T]

    model = Model[int](field=[5])
    assert model.field[0] == 5

    with pytest.raises(ValidationError):
        model = Model[int](field=['a'])


def test_generic_annotated():
    T = TypeVar('T')

    class SomeGenericModel(BaseModel, Generic[T]):
        some_field: Annotated[T, Field(alias='the_alias')]

    SomeGenericModel[str](the_alias='qwe')


def test_generic_subclass():
    T = TypeVar('T')

    class A(BaseModel, Generic[T]): ...

    class B(A[T], Generic[T]): ...

    class C(B[T], Generic[T]): ...

    assert B[int].__name__ == 'B[int]'
    assert issubclass(B[int], B)
    assert issubclass(B[int], A)
    assert not issubclass(B[int], C)


def test_generic_subclass_with_partial_application():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(BaseModel, Generic[T]): ...

    class B(A[S], Generic[T, S]): ...

    PartiallyAppliedB = B[str, T]
    assert issubclass(PartiallyAppliedB[int], A)


def test_multilevel_generic_binding():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(BaseModel, Generic[T, S]): ...

    class B(A[str, T], Generic[T]): ...

    assert B[int].__name__ == 'B[int]'
    assert issubclass(B[int], A)


def test_generic_subclass_with_extra_type():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(BaseModel, Generic[T]): ...

    class B(A[S], Generic[T, S]): ...

    assert B[int, str].__name__ == 'B[int, str]', B[int, str].__name__
    assert issubclass(B[str, int], B)
    assert issubclass(B[str, int], A)


def test_generic_subclass_with_extra_type_requires_all_params():
    T = TypeVar('T')
    S = TypeVar('S')

    class A(BaseModel, Generic[T]): ...

    with pytest.raises(
        TypeError,
        match=re.escape(
            'All parameters must be present on typing.Generic; you should inherit from typing.Generic[~T, ~S]'
        ),
    ):

        class B(A[T], Generic[S]): ...


def test_generic_subclass_with_extra_type_with_hint_message():
    E = TypeVar('E', bound=BaseModel)
    D = TypeVar('D')

    with pytest.warns(
        GenericBeforeBaseModelWarning,
        match='Classes should inherit from `BaseModel` before generic classes',
    ):

        class BaseGenericClass(Generic[E, D], BaseModel):
            uid: str
            name: str

    with pytest.raises(
        TypeError,
        match=re.escape(
            'All parameters must be present on typing.Generic; you should inherit from typing.Generic[~E, ~D].'
            ' Note: `typing.Generic` must go last:'
            ' `class ChildGenericClass(BaseGenericClass, typing.Generic[~E, ~D]): ...`'
        ),
    ):
        with pytest.warns(
            GenericBeforeBaseModelWarning,
            match='Classes should inherit from `BaseModel` before generic classes',
        ):

            class ChildGenericClass(BaseGenericClass[E, Dict[str, Any]]): ...


def test_multi_inheritance_generic_binding():
    T = TypeVar('T')

    class A(BaseModel, Generic[T]): ...

    class B(A[int], Generic[T]): ...

    class C(B[str], Generic[T]): ...

    assert C[float].__name__ == 'C[float]'
    assert issubclass(C[float], B)
    assert issubclass(C[float], A)
    assert not issubclass(B[float], C)


def test_parent_field_parametrization():
    T = TypeVar('T')

    class A(BaseModel, Generic[T]):
        a: T

    class B(A, Generic[T]):
        b: T

    with pytest.raises(ValidationError) as exc_info:
        B[int](a='a', b=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_multi_inheritance_generic_defaults():
    T = TypeVar('T')

    class A(BaseModel, Generic[T]):
        a: T
        x: str = 'a'

    class B(A[int], Generic[T]):
        b: Optional[T] = None
        y: str = 'b'

    class C(B[str], Generic[T]):
        c: T
        z: str = 'c'

    assert C(a=1, c=...).model_dump() == {'a': 1, 'b': None, 'c': ..., 'x': 'a', 'y': 'b', 'z': 'c'}


def test_parse_generic_json():
    T = TypeVar('T')

    class MessageWrapper(BaseModel, Generic[T]):
        message: Json[T]

    class Payload(BaseModel):
        payload_field: str

    raw = json.dumps({'payload_field': 'payload'})
    record = MessageWrapper[Payload](message=raw)
    assert isinstance(record.message, Payload)

    validation_schema = record.model_json_schema(mode='validation')
    assert validation_schema == {
        '$defs': {
            'Payload': {
                'properties': {'payload_field': {'title': 'Payload Field', 'type': 'string'}},
                'required': ['payload_field'],
                'title': 'Payload',
                'type': 'object',
            }
        },
        'properties': {
            'message': {
                'contentMediaType': 'application/json',
                'contentSchema': {'$ref': '#/$defs/Payload'},
                'title': 'Message',
                'type': 'string',
            }
        },
        'required': ['message'],
        'title': 'MessageWrapper[test_parse_generic_json.<locals>.Payload]',
        'type': 'object',
    }

    serialization_schema = record.model_json_schema(mode='serialization')
    assert serialization_schema == {
        '$defs': {
            'Payload': {
                'properties': {'payload_field': {'title': 'Payload Field', 'type': 'string'}},
                'required': ['payload_field'],
                'title': 'Payload',
                'type': 'object',
            }
        },
        'properties': {'message': {'allOf': [{'$ref': '#/$defs/Payload'}], 'title': 'Message'}},
        'required': ['message'],
        'title': 'MessageWrapper[test_parse_generic_json.<locals>.Payload]',
        'type': 'object',
    }


@pytest.mark.skipif(sys.version_info > (3, 12), reason="memray doesn't yet support Python 3.13")
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

    class MyModel(BaseModel, Generic[T, U, V]):
        message: Json[T]
        field: Dict[U, V]

    class Outer(BaseModel, Generic[T]):
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


@pytest.mark.xfail(reason='Generic models are not type aliases', raises=TypeError)
def test_generic_model_as_parameter_to_generic_type_alias() -> None:
    T = TypeVar('T')

    class GenericPydanticModel(BaseModel, Generic[T]):
        x: T

    GenericPydanticModelList = List[GenericPydanticModel[T]]
    GenericPydanticModelList[int]


def test_double_typevar_substitution() -> None:
    T = TypeVar('T')

    class GenericPydanticModel(BaseModel, Generic[T]):
        x: T = []

    assert GenericPydanticModel[List[T]](x=[1, 2, 3]).model_dump() == {'x': [1, 2, 3]}


@pytest.fixture(autouse=True)
def ensure_contextvar_gets_reset():
    # Ensure that the generic recursion contextvar is empty at the start of every test
    assert not recursively_defined_type_refs()


def test_generic_recursion_contextvar():
    T = TypeVar('T')

    class TestingException(Exception):
        pass

    class Model(BaseModel, Generic[T]):
        pass

    # Make sure that the contextvar-managed recursive types cache begins empty
    assert not recursively_defined_type_refs()
    try:
        with generic_recursion_self_type(Model, (int,)):
            # Make sure that something has been added to the contextvar-managed recursive types cache
            assert recursively_defined_type_refs()
            raise TestingException
    except TestingException:
        pass

    # Make sure that an exception causes the contextvar-managed recursive types cache to be reset
    assert not recursively_defined_type_refs()


def test_limited_dict():
    d = LimitedDict(10)
    d[1] = '1'
    d[2] = '2'
    assert list(d.items()) == [(1, '1'), (2, '2')]
    for no in '34567890':
        d[int(no)] = no
    assert list(d.items()) == [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (0, '0'),
    ]
    d[11] = '11'

    # reduce size to 9 after setting 11
    assert len(d) == 9
    assert list(d.items()) == [
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (0, '0'),
        (11, '11'),
    ]
    d[12] = '12'
    assert len(d) == 10
    d[13] = '13'
    assert len(d) == 9


def test_construct_generic_model_with_validation():
    T = TypeVar('T')

    class Page(BaseModel, Generic[T]):
        page: int = Field(ge=42)
        items: Sequence[T]
        unenforced: PositiveInt = Field(..., lt=10)

    with pytest.raises(ValidationError) as exc_info:
        Page[int](page=41, items=[], unenforced=11)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'ge': 42},
            'input': 41,
            'loc': ('page',),
            'msg': 'Input should be greater than or equal to 42',
            'type': 'greater_than_equal',
        },
        {
            'ctx': {'lt': 10},
            'input': 11,
            'loc': ('unenforced',),
            'msg': 'Input should be less than 10',
            'type': 'less_than',
        },
    ]


def test_construct_other_generic_model_with_validation():
    # based on the test-case from https://github.com/samuelcolvin/pydantic/issues/2581
    T = TypeVar('T')

    class Page(BaseModel, Generic[T]):
        page: int = Field(ge=42)
        items: Sequence[T]

    # Check we can perform this assignment, this is the actual test
    concrete_model = Page[str]
    print(concrete_model)
    assert concrete_model.__name__ == 'Page[str]'

    # Sanity check the resulting type works as expected
    valid = concrete_model(page=42, items=[])
    assert valid.page == 42

    with pytest.raises(ValidationError) as exc_info:
        concrete_model(page=41, items=[])
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'ge': 42},
            'input': 41,
            'loc': ('page',),
            'msg': 'Input should be greater than or equal to 42',
            'type': 'greater_than_equal',
        }
    ]


def test_generic_enum_bound():
    T = TypeVar('T', bound=Enum)

    class MyEnum(Enum):
        a = 1

    class OtherEnum(Enum):
        b = 2

    class Model(BaseModel, Generic[T]):
        x: T

    m = Model(x=MyEnum.a)
    assert m.x == MyEnum.a

    with pytest.raises(ValidationError) as exc_info:
        Model(x=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'Enum'},
            'input': 1,
            'loc': ('x',),
            'msg': 'Input should be an instance of Enum',
            'type': 'is_instance_of',
        }
    ]

    m2 = Model[MyEnum](x=MyEnum.a)
    assert m2.x == MyEnum.a

    with pytest.raises(ValidationError) as exc_info:
        Model[MyEnum](x=OtherEnum.b)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'expected': '1'},
            'input': OtherEnum.b,
            'loc': ('x',),
            'msg': 'Input should be 1',
            'type': 'enum',
        }
    ]

    # insert_assert(Model[MyEnum].model_json_schema())
    assert Model[MyEnum].model_json_schema() == {
        '$defs': {'MyEnum': {'const': 1, 'enum': [1], 'title': 'MyEnum', 'type': 'integer'}},
        'properties': {'x': {'$ref': '#/$defs/MyEnum'}},
        'required': ['x'],
        'title': 'Model[test_generic_enum_bound.<locals>.MyEnum]',
        'type': 'object',
    }


def test_generic_intenum_bound():
    T = TypeVar('T', bound=IntEnum)

    class MyEnum(IntEnum):
        a = 1

    class OtherEnum(IntEnum):
        b = 2

    class Model(BaseModel, Generic[T]):
        x: T

    m = Model(x=MyEnum.a)
    assert m.x == MyEnum.a

    with pytest.raises(ValidationError) as exc_info:
        Model(x=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'IntEnum'},
            'input': 1,
            'loc': ('x',),
            'msg': 'Input should be an instance of IntEnum',
            'type': 'is_instance_of',
        }
    ]

    m2 = Model[MyEnum](x=MyEnum.a)
    assert m2.x == MyEnum.a

    with pytest.raises(ValidationError) as exc_info:
        Model[MyEnum](x=OtherEnum.b)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'expected': '1'},
            'input': 2,
            'loc': ('x',),
            'msg': 'Input should be 1',
            'type': 'enum',
        }
    ]

    # insert_assert(Model[MyEnum].model_json_schema())
    assert Model[MyEnum].model_json_schema() == {
        '$defs': {'MyEnum': {'const': 1, 'enum': [1], 'title': 'MyEnum', 'type': 'integer'}},
        'properties': {'x': {'$ref': '#/$defs/MyEnum'}},
        'required': ['x'],
        'title': 'Model[test_generic_intenum_bound.<locals>.MyEnum]',
        'type': 'object',
    }


@pytest.mark.skipif(sys.version_info < (3, 11), reason='requires python 3.11 or higher')
@pytest.mark.xfail(
    reason='TODO: Variadic generic parametrization is not supported yet;'
    ' Issue: https://github.com/pydantic/pydantic/issues/5804'
)
def test_variadic_generic_init():
    class ComponentModel(BaseModel):
        pass

    class Wrench(ComponentModel):
        pass

    class Screwdriver(ComponentModel):
        pass

    ComponentVar = TypeVar('ComponentVar', bound=ComponentModel)
    NumberOfComponents = TypeVarTuple('NumberOfComponents')

    class VariadicToolbox(BaseModel, Generic[ComponentVar, Unpack[NumberOfComponents]]):
        main_component: ComponentVar
        left_component_pocket: Optional[list[ComponentVar]] = Field(default_factory=list)
        right_component_pocket: Optional[list[ComponentVar]] = Field(default_factory=list)

        @computed_field
        @property
        def all_components(self) -> tuple[ComponentVar, Unpack[NumberOfComponents]]:
            return (self.main_component, *self.left_component_pocket, *self.right_component_pocket)

    sa, sb, w = Screwdriver(), Screwdriver(), Wrench()
    my_toolbox = VariadicToolbox[Screwdriver, Screwdriver, Wrench](
        main_component=sa, left_component_pocket=[w], right_component_pocket=[sb]
    )

    assert my_toolbox.all_components == [sa, w, sb]


@pytest.mark.skipif(sys.version_info < (3, 11), reason='requires python 3.11 or higher')
@pytest.mark.xfail(
    reason='TODO: Variadic fields are not supported yet; Issue: https://github.com/pydantic/pydantic/issues/5804'
)
def test_variadic_generic_with_variadic_fields():
    class ComponentModel(BaseModel):
        pass

    class Wrench(ComponentModel):
        pass

    class Screwdriver(ComponentModel):
        pass

    ComponentVar = TypeVar('ComponentVar', bound=ComponentModel)
    NumberOfComponents = TypeVarTuple('NumberOfComponents')

    class VariadicToolbox(BaseModel, Generic[ComponentVar, Unpack[NumberOfComponents]]):
        toolbelt_cm_size: Optional[tuple[Unpack[NumberOfComponents]]] = Field(default_factory=tuple)
        manual_toolset: Optional[tuple[ComponentVar, Unpack[NumberOfComponents]]] = Field(default_factory=tuple)

    MyToolboxClass = VariadicToolbox[Screwdriver, Screwdriver, Wrench]

    sa, sb, w = Screwdriver(), Screwdriver(), Wrench()
    MyToolboxClass(toolbelt_cm_size=(5, 10.5, 4), manual_toolset=(sa, sb, w))

    with pytest.raises(TypeError):
        # Should raise error because integer 5 does not meet the bound requirements of ComponentVar
        MyToolboxClass(manual_toolset=(sa, sb, 5))


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason=(
        'Multiple inheritance with NamedTuple and the corresponding type annotations'
        " aren't supported before Python 3.11"
    ),
)
def test_generic_namedtuple():
    T = TypeVar('T')

    class FlaggedValue(NamedTuple, Generic[T]):
        value: T
        flag: bool

    class Model(BaseModel):
        f_value: FlaggedValue[float]

    assert Model(f_value=(1, True)).model_dump() == {'f_value': (1, True)}
    with pytest.raises(ValidationError):
        Model(f_value=(1, 'abc'))
    with pytest.raises(ValidationError):
        Model(f_value=('abc', True))


def test_generic_none():
    T = TypeVar('T')

    class Container(BaseModel, Generic[T]):
        value: T

    assert Container[type(None)](value=None).value is None
    assert Container[None](value=None).value is None


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='PyPy does not allow ParamSpec in generics')
def test_paramspec_is_usable():
    # This used to cause a recursion error due to `P in P is True`
    # This test doesn't actually test that ParamSpec works properly for validation or anything.

    P = ParamSpec('P')

    class MyGenericParamSpecClass(Generic[P]):
        def __init__(self, func: Callable[P, None], *args: P.args, **kwargs: P.kwargs) -> None:
            super().__init__()

    class ParamSpecGenericModel(BaseModel, Generic[P]):
        my_generic: MyGenericParamSpecClass[P]

        model_config = dict(arbitrary_types_allowed=True)


def test_parametrize_with_basemodel():
    T = TypeVar('T')

    class SimpleGenericModel(BaseModel, Generic[T]):
        pass

    class Concrete(SimpleGenericModel[BaseModel]):
        pass


def test_no_generic_base():
    T = TypeVar('T')

    class A(BaseModel, Generic[T]):
        a: T

    class B(A[T]):
        b: T

    class C(B[int]):
        pass

    assert C(a='1', b='2').model_dump() == {'a': 1, 'b': 2}
    with pytest.raises(ValidationError) as exc_info:
        C(a='a', b='b')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        },
        {
            'input': 'b',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        },
    ]


def test_reverse_order_generic_hashability():
    T = TypeVar('T')

    with pytest.warns(
        GenericBeforeBaseModelWarning,
        match='Classes should inherit from `BaseModel` before generic classes',
    ):

        class Model(Generic[T], BaseModel):
            x: T
            model_config = dict(frozen=True)

    m1 = Model[int](x=1)
    m2 = Model[int](x=1)
    assert len({m1, m2}) == 1


def test_serialize_unsubstituted_typevars_bound() -> None:
    class ErrorDetails(BaseModel):
        foo: str

    # This version of `TypeVar` does not support `default` on Python <3.12
    ErrorDataT = TypeVar('ErrorDataT', bound=ErrorDetails)

    class Error(BaseModel, Generic[ErrorDataT]):
        message: str
        details: ErrorDataT

    class MyErrorDetails(ErrorDetails):
        bar: str

    sample_error = Error(
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
            'bar': 'baz',
        },
    }

    sample_error = Error[ErrorDetails](
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
        },
    }

    sample_error = Error[MyErrorDetails](
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
            'bar': 'baz',
        },
    }


def test_serialize_unsubstituted_typevars_bound_default_supported() -> None:
    class ErrorDetails(BaseModel):
        foo: str

    # This version of `TypeVar` always support `default`
    ErrorDataT = TypingExtensionsTypeVar('ErrorDataT', bound=ErrorDetails)

    class Error(BaseModel, Generic[ErrorDataT]):
        message: str
        details: ErrorDataT

    class MyErrorDetails(ErrorDetails):
        bar: str

    sample_error = Error(
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
            'bar': 'baz',
        },
    }

    sample_error = Error[ErrorDetails](
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
        },
    }

    sample_error = Error[MyErrorDetails](
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
            'bar': 'baz',
        },
    }


@pytest.mark.parametrize(
    'type_var',
    [
        TypingExtensionsTypeVar('ErrorDataT', default=BaseModel),
        TypeVar('ErrorDataT', BaseModel, str),
    ],
    ids=['default', 'constraint'],
)
def test_serialize_unsubstituted_typevars_variants(
    type_var: Type[BaseModel],
) -> None:
    class ErrorDetails(BaseModel):
        foo: str

    class Error(BaseModel, Generic[type_var]):  # type: ignore
        message: str
        details: type_var

    class MyErrorDetails(ErrorDetails):
        bar: str

    sample_error = Error(
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {},
    }

    sample_error = Error[ErrorDetails](
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
        },
    }

    sample_error = Error[MyErrorDetails](
        message='We just had an error',
        details=MyErrorDetails(foo='var', bar='baz'),
    )
    assert sample_error.details.model_dump() == {
        'foo': 'var',
        'bar': 'baz',
    }
    assert sample_error.model_dump() == {
        'message': 'We just had an error',
        'details': {
            'foo': 'var',
            'bar': 'baz',
        },
    }


def test_mix_default_and_constraints() -> None:
    T = TypingExtensionsTypeVar('T', str, int, default=str)

    msg = 'Pydantic does not support mixing more than one of TypeVar bounds, constraints and defaults'
    with pytest.raises(NotImplementedError, match=msg):

        class _(BaseModel, Generic[T]):
            x: T


def test_generic_with_not_required_in_typed_dict() -> None:
    T = TypingExtensionsTypeVar('T')

    class FooStr(TypedDict):
        type: NotRequired[str]

    class FooGeneric(TypedDict, Generic[T]):
        type: NotRequired[T]

    ta_foo_str = TypeAdapter(FooStr)
    assert ta_foo_str.validate_python({'type': 'tomato'}) == {'type': 'tomato'}
    assert ta_foo_str.validate_python({}) == {}
    ta_foo_generic = TypeAdapter(FooGeneric[str])
    assert ta_foo_generic.validate_python({'type': 'tomato'}) == {'type': 'tomato'}
    assert ta_foo_generic.validate_python({}) == {}


def test_generic_with_allow_extra():
    T = TypeVar('T')

    # This used to raise an error related to accessing the __annotations__ attribute of the Generic class
    class AllowExtraGeneric(BaseModel, Generic[T], extra='allow'):
        data: T
