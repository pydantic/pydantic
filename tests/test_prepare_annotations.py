from dataclasses import dataclass
from typing import Any, Iterator, List, Sequence

import dirty_equals as de
import pytest
from annotated_types import Gt, Lt
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import TypeAdapter
from pydantic.annotated import GetCoreSchemaHandler
from pydantic.validators import AfterValidator
from pydantic.errors import PydanticSchemaGenerationError
from pydantic.json_schema import GetJsonSchemaHandler, JsonSchemaValue


@dataclass
class MetadataApplier:
    inner_core_schema: CoreSchema
    outer_core_schema: CoreSchema

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.outer_core_schema

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(self.inner_core_schema)


class MyDecimal(float):
    """
    An example of what a user would need to do if they wanted to implement something that
    behaves like Decimal (aside from the fact that we special case Decimal).
    """

    @classmethod
    def __prepare_pydantic_annotations__(cls, source_type: Any, annotations: Sequence[Any]) -> Sequence[Any]:
        assert source_type is MyDecimal
        metadata: dict[str, Any] = {}
        remaining_annotations: list[Any] = []
        for annotation in annotations:
            if isinstance(annotation, Gt):
                metadata['gt'] = annotation.gt
            else:
                remaining_annotations.append(annotation)
        inner_schema = core_schema.float_schema(**metadata)
        outer_schema = core_schema.no_info_after_validator_function(MyDecimal, inner_schema)
        new_annotations = [
            source_type,
            MetadataApplier(inner_core_schema=inner_schema, outer_core_schema=outer_schema),
            *remaining_annotations,
        ]
        return new_annotations


def test_decimal_like_in_annotated() -> None:
    def no_op_val(x: Any) -> Any:
        return x

    a = TypeAdapter(List[Annotated[MyDecimal, Gt(10), AfterValidator(no_op_val)]])

    expected = de.IsPartialDict(
        core_schema.list_schema(
            de.IsPartialDict(
                core_schema.no_info_after_validator_function(
                    no_op_val,
                    de.IsPartialDict(
                        core_schema.no_info_after_validator_function(
                            MyDecimal, de.IsPartialDict(core_schema.float_schema(gt=10))
                        )
                    ),
                )
            )
        )
    )

    assert a.core_schema == expected


def test_decimal_like_outside_of_annotated() -> None:
    a = TypeAdapter(List[MyDecimal])

    expected = de.IsPartialDict(
        core_schema.list_schema(
            de.IsPartialDict(
                core_schema.no_info_after_validator_function(MyDecimal, de.IsPartialDict(core_schema.float_schema()))
            )
        )
    )

    assert a.core_schema == expected


def test_return_no_annotations_in_annotated() -> None:
    class MyType(int):
        @classmethod
        def __prepare_pydantic_annotations__(cls, source_type: Any, annotations: Sequence[Any]) -> List[Any]:
            return []

    msg = 'Custom types must return at least 1 item since the first item is the replacement source type'

    with pytest.raises(PydanticSchemaGenerationError, match=msg):
        TypeAdapter(Annotated[MyType, Gt(0)])

    with pytest.raises(PydanticSchemaGenerationError, match=msg):
        TypeAdapter(MyType)


def test_generator_custom_type() -> None:
    class MyType(int):
        @classmethod
        def __prepare_pydantic_annotations__(cls, source_type: Any, annotations: Sequence[Any]) -> Iterator[Any]:
            assert source_type is MyType
            yield int
            yield Gt(123)
            yield from annotations

    a = TypeAdapter(MyType)
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123))

    a = TypeAdapter(Annotated[MyType, Lt(420)])
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123, lt=420))


def test_returns_itself_called_only_once() -> None:
    """
    If `__prepare_pydantic_annotations__` returns something that implements `__prepare_pydantic_annotations__`
    (including itself) we don't recurse infinitely.
    """
    calls: list[Any] = []

    class MyType(int):
        @classmethod
        def __prepare_pydantic_annotations__(cls, source_type: Any, annotations: Sequence[Any]) -> Iterator[Any]:
            calls.append(cls.__prepare_pydantic_annotations__)
            # we return ourselves as the first annotation
            # this may be fine if the thing implements `__get_pydantic_core_schema__` as well
            # (although I'm not sure why you'd want to do that)
            # but at the very least we should _not_ fail with a recursion error
            # which is easy to have happen because we'd just call this method again in GenerateSchema's
            # next iteration
            yield cls
            yield from annotations

    msg = (
        'Unable to generate pydantic-core schema for'
        f" <class '{__name__}.test_returns_itself_called_only_once.<locals>.MyType'>"
    )
    with pytest.raises(PydanticSchemaGenerationError, match=msg):
        TypeAdapter(MyType)

    assert calls == [MyType.__prepare_pydantic_annotations__]
    calls.clear()

    class MyTypeGood(MyType):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            calls.append(cls.__get_pydantic_core_schema__)
            assert source_type == MyTypeGood
            return handler(int)

    a = TypeAdapter(MyTypeGood)
    assert a.core_schema == core_schema.int_schema()

    assert calls == [MyTypeGood.__prepare_pydantic_annotations__, MyTypeGood.__get_pydantic_core_schema__]
