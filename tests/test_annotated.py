import datetime as dt
import sys
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterator, List, Optional, Set, TypeVar

import pytest
import pytz
from annotated_types import BaseMetadata, GroupedMetadata, Gt, Lt, Predicate
from pydantic_core import CoreSchema, PydanticUndefined, core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, Field, GetCoreSchemaHandler, PydanticUserError, TypeAdapter, ValidationError
from pydantic.errors import PydanticSchemaGenerationError
from pydantic.fields import PrivateAttr
from pydantic.functional_validators import AfterValidator

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
            PydanticUndefined,
            'FieldInfo(annotation=int, required=True, metadata=[Gt(gt=0)])',
        ),
        (
            lambda: Annotated[int, Field(gt=0), Lt(2)],
            5,
            'FieldInfo(annotation=int, required=False, default=5, metadata=[Gt(gt=0), Lt(lt=2)])',
        ),
        (
            lambda: Annotated[int, Field(alias='foobar')],
            PydanticUndefined,
            "FieldInfo(annotation=int, required=True, alias='foobar', alias_priority=2)",
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
            PydanticUndefined,
            pytest.raises(ValueError, match=r'Field required \[type=missing,'),
        ),
        (
            lambda: Annotated[int, Field()],
            PydanticUndefined,
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
        'e': "FieldInfo(annotation=List[Annotated[str, FieldInfo(annotation=NoneType, required=True, metadata=[MaxLen(max_length=3)])]], required=True, description='foo')",
    }
    assert MyModel(b='def', e=['xyz']).model_dump() == dict(a='abc', b='def', c=2, d=2, e=['xyz'])


def test_modify_get_schema_annotated() -> None:
    calls: List[str] = []

    class CustomType:
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            calls.append('CustomType:before')
            with pytest.raises(PydanticSchemaGenerationError):
                handler(source)
            schema = core_schema.no_info_plain_validator_function(lambda _: CustomType())
            calls.append('CustomType:after')
            return schema

    class PydanticMetadata:
        def __get_pydantic_core_schema__(self, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            calls.append('PydanticMetadata:before')
            schema = handler(source)
            calls.append('PydanticMetadata:after')
            return schema

    class GroupedMetadataMarker(GroupedMetadata):
        def __iter__(self) -> Iterator[BaseMetadata]:
            # no way to actually hook into schema building
            # so just register when our iter is called
            calls.append('GroupedMetadataMarker:iter')
            yield from []

    class _(BaseModel):
        x: Annotated[CustomType, GroupedMetadataMarker(), PydanticMetadata()]

    # insert_assert(calls)
    assert calls == [
        'GroupedMetadataMarker:iter',
        'PydanticMetadata:before',
        'CustomType:before',
        'CustomType:after',
        'PydanticMetadata:after',
    ]

    calls.clear()

    class _(BaseModel):
        x: Annotated[CustomType, PydanticMetadata(), GroupedMetadataMarker()]

    # insert_assert(calls)
    assert calls == [
        'GroupedMetadataMarker:iter',
        'PydanticMetadata:before',
        'CustomType:before',
        'CustomType:after',
        'PydanticMetadata:after',
    ]

    calls.clear()


def test_annotated_alias_at_low_level() -> None:
    with pytest.warns(
        UserWarning,
        match=r'`alias` specification on field "low_level_alias_field" must be set on outermost annotation to take effect.',
    ):

        class Model(BaseModel):
            low_level_alias_field: Optional[Annotated[int, Field(alias='field_alias')]] = None

    assert Model(field_alias=1).low_level_alias_field is None


def test_get_pydantic_core_schema_source_type() -> None:
    types: Set[Any] = set()

    class PydanticMarker:
        def __get_pydantic_core_schema__(self, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            types.add(source)
            return handler(source)

    class _(BaseModel):
        x: Annotated[Annotated[int, 'foo'], PydanticMarker()]

    assert types == {int}
    types.clear()

    T = TypeVar('T')

    class GenericModel(BaseModel, Generic[T]):
        y: T

    class _(BaseModel):
        x: Annotated[GenericModel[int], PydanticMarker()]

    assert types == {GenericModel[int]}
    types.clear()


def test_merge_field_infos_type_adapter() -> None:
    ta = TypeAdapter(
        Annotated[
            int, Field(gt=0), Field(lt=100), Field(gt=1), Field(description='abc'), Field(3), Field(description=None)
        ]
    )

    default = ta.get_default_value()
    assert default is not None
    assert default.value == 3

    # insert_assert(ta.validate_python(2))
    assert ta.validate_python(2) == 2

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'greater_than', 'loc': (), 'msg': 'Input should be greater than 1', 'input': 1, 'ctx': {'gt': 1}}
    ]

    # insert_assert(ta.json_schema())
    assert ta.json_schema() == {
        'default': 3,
        'description': 'abc',
        'exclusiveMaximum': 100,
        'exclusiveMinimum': 1,
        'type': 'integer',
    }


def test_merge_field_infos_model() -> None:
    class Model(BaseModel):
        x: Annotated[
            int, Field(gt=0), Field(lt=100), Field(gt=1), Field(description='abc'), Field(3), Field(description=None)
        ] = Field(5)

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'properties': {
            'x': {'default': 5, 'exclusiveMaximum': 100, 'exclusiveMinimum': 1, 'title': 'X', 'type': 'integer'}
        },
        'title': 'Model',
        'type': 'object',
    }


def test_model_dump_doesnt_dump_annotated_dunder():
    class Model(BaseModel):
        one: int

    AnnotatedModel = Annotated[Model, ...]

    # In Pydantic v1, `AnnotatedModel.dict()` would have returned
    # `{'one': 1, '__orig_class__': typing.Annotated[...]}`
    assert AnnotatedModel(one=1).model_dump() == {'one': 1}


def test_merge_field_infos_ordering() -> None:
    TheType = Annotated[int, AfterValidator(lambda x: x), Field(le=2), AfterValidator(lambda x: x * 2), Field(lt=4)]

    class Model(BaseModel):
        x: TheType

    assert Model(x=1).x == 2

    with pytest.raises(ValidationError) as exc_info:
        Model(x=2)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'less_than', 'loc': ('x',), 'msg': 'Input should be less than 4', 'input': 2, 'ctx': {'lt': 4}}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'less_than_equal',
            'loc': ('x',),
            'msg': 'Input should be less than or equal to 2',
            'input': 3,
            'ctx': {'le': 2},
        }
    ]


def test_validate_float_inf_nan_python() -> None:
    ta = TypeAdapter(Annotated[float, AfterValidator(lambda x: x * 3), Field(allow_inf_nan=False)])
    assert ta.validate_python(2.0) == 6.0

    ta = TypeAdapter(Annotated[float, AfterValidator(lambda _: float('nan')), Field(allow_inf_nan=False)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1.0)

    # insert_assert(exc_info.value.errors(include_url=False))
    # TODO: input should be float('nan'), this seems like a subtle bug in pydantic-core
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': 1.0}
    ]


def test_predicate_error_python() -> None:
    ta = TypeAdapter(Annotated[int, Predicate(lambda x: x > 0)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(-1)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'predicate_failed',
            'loc': (),
            'msg': 'Predicate test_predicate_error_python.<locals>.<lambda> failed',
            'input': -1,
        }
    ]


def test_annotated_field_info_not_lost_from_forwardref():
    from pydantic import BaseModel

    class ForwardRefAnnotatedFieldModel(BaseModel):
        foo: 'Annotated[Integer, Field(alias="bar", default=1)]' = 2
        foo2: 'Annotated[Integer, Field(alias="bar2", default=1)]' = Field(default=2, alias='baz')

    Integer = int

    ForwardRefAnnotatedFieldModel.model_rebuild()

    assert ForwardRefAnnotatedFieldModel(bar=3).foo == 3
    assert ForwardRefAnnotatedFieldModel(baz=3).foo2 == 3

    with pytest.raises(ValidationError) as exc_info:
        ForwardRefAnnotatedFieldModel(bar='bar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'bar',
            'loc': ('bar',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_annotated_private_field_with_default():
    class AnnotatedPrivateFieldModel(BaseModel):
        _foo: Annotated[int, PrivateAttr(default=1)]
        _bar: Annotated[str, 'hello']

    model = AnnotatedPrivateFieldModel()
    assert model._foo == 1

    assert model.__pydantic_private__ == {'_foo': 1}

    with pytest.raises(AttributeError):
        assert model._bar

    model._bar = 'world'
    assert model._bar == 'world'
    assert model.__pydantic_private__ == {'_foo': 1, '_bar': 'world'}

    with pytest.raises(AttributeError):
        assert model.bar


def test_min_length_field_info_not_lost():
    class AnnotatedFieldModel(BaseModel):
        foo: 'Annotated[String, Field(min_length=3)]' = Field(description='hello')

    String = str

    AnnotatedFieldModel.model_rebuild()

    assert AnnotatedFieldModel(foo='000').foo == '000'

    with pytest.raises(ValidationError) as exc_info:
        AnnotatedFieldModel(foo='00')

    assert exc_info.value.errors(include_url=False) == [
        {
            'loc': ('foo',),
            'input': '00',
            'ctx': {'min_length': 3},
            'msg': 'String should have at least 3 characters',
            'type': 'string_too_short',
        }
    ]

    # Ensure that the inner annotation does not override the outer, even for metadata:
    class AnnotatedFieldModel2(BaseModel):
        foo: 'Annotated[String, Field(min_length=3)]' = Field(description='hello', min_length=2)

    AnnotatedFieldModel2(foo='00')

    class AnnotatedFieldModel4(BaseModel):
        foo: 'Annotated[String, Field(min_length=3)]' = Field(description='hello', min_length=4)

    with pytest.raises(ValidationError) as exc_info:
        AnnotatedFieldModel4(foo='00')

    assert exc_info.value.errors(include_url=False) == [
        {
            'loc': ('foo',),
            'input': '00',
            'ctx': {'min_length': 4},
            'msg': 'String should have at least 4 characters',
            'type': 'string_too_short',
        }
    ]


def test_tzinfo_validator_example_pattern() -> None:
    """Test that tzinfo custom validator pattern works as explained in the examples/validators docs."""

    @dataclass(frozen=True)
    class MyDatetimeValidator:
        tz_constraint: Optional[str] = None

        def tz_constraint_validator(
            self,
            value: dt.datetime,
            handler: Callable,  # (1)!
        ):
            """Validate tz_constraint and tz_info."""
            # handle naive datetimes
            if self.tz_constraint is None:
                assert value.tzinfo is None, 'tz_constraint is None, but provided value is tz-aware.'
                return handler(value)

            # validate tz_constraint and tz-aware tzinfo
            if self.tz_constraint not in pytz.all_timezones:
                raise PydanticUserError(
                    f'Invalid tz_constraint: {self.tz_constraint}', code='unevaluable-type-annotation'
                )
            result = handler(value)  # (2)!
            assert self.tz_constraint == str(
                result.tzinfo
            ), f'Invalid tzinfo: {str(result.tzinfo)}, expected: {self.tz_constraint}'

            return result

        def __get_pydantic_core_schema__(
            self,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            return core_schema.no_info_wrap_validator_function(
                self.tz_constraint_validator,
                handler(source_type),
            )

    LA = 'America/Los_Angeles'

    # passing naive test
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator()])
    ta.validate_python(dt.datetime.now())

    # failing naive test
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator()])
    with pytest.raises(Exception):
        ta.validate_python(dt.datetime.now(pytz.timezone(LA)))

    # passing tz-aware test
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
    ta.validate_python(dt.datetime.now(pytz.timezone(LA)))

    # failing bad tz
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator('foo')])
    with pytest.raises(Exception):
        ta.validate_python(dt.datetime.now())

    # failing tz-aware test
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
    with pytest.raises(Exception):
        ta.validate_python(dt.datetime.now())


def test_utcoffset_validator_example_pattern() -> None:
    """Test that utcoffset custom validator pattern works as explained in the examples/validators docs."""

    @dataclass(frozen=True)
    class MyDatetimeValidator:
        lower_bound: int
        upper_bound: int

        def validate_tz_bounds(self, value: dt.datetime, handler: Callable):
            """Validate and test bounds"""
            assert value.utcoffset() is not None, 'UTC offset must exist'
            assert self.lower_bound <= self.upper_bound, 'Invalid bounds'

            result = handler(value)

            hours_offset = value.utcoffset().total_seconds() / 3600
            assert self.lower_bound <= hours_offset <= self.upper_bound, 'Value out of bounds'

            return result

        def __get_pydantic_core_schema__(
            self,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            return core_schema.no_info_wrap_validator_function(
                self.validate_tz_bounds,
                handler(source_type),
            )

    LA = 'America/Los_Angeles'

    # test valid bound passing
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-10, 10)])
    ta.validate_python(dt.datetime.now(pytz.timezone(LA)))

    # test valid bound failing - missing TZ
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-12, 12)])
    with pytest.raises(Exception):
        ta.validate_python(dt.datetime.now())

    # test invalid bound
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(0, 4)])
    with pytest.raises(Exception):
        ta.validate_python(dt.datetime.now(pytz.timezone(LA)))
