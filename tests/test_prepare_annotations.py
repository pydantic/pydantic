from dataclasses import dataclass
from typing import Annotated, Any, Iterator, List, Sequence

import dirty_equals as de
import pytest
from annotated_types import Gt, Lt
from pydantic_core import CoreSchema, core_schema

from pydantic.analyzed_type import AnalyzedType
from pydantic.annotated import GetCoreSchemaHandler
from pydantic.annotated_arguments import AfterValidator
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

    a = AnalyzedType(List[Annotated[MyDecimal, Gt(10), AfterValidator(no_op_val)]])

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
    a = AnalyzedType(List[MyDecimal])

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

    msg = 'You must return at least 1 item since the first item is the replacement source type'

    with pytest.raises(PydanticSchemaGenerationError, match=msg):
        AnalyzedType(Annotated[MyType, Gt(0)])

    with pytest.raises(PydanticSchemaGenerationError, match=msg):
        AnalyzedType(MyType)


def test_generator_custom_type() -> None:
    class MyType(int):
        @classmethod
        def __prepare_pydantic_annotations__(self, source_type: Any, annotations: Sequence[Any]) -> Iterator[Any]:
            assert source_type is MyType
            yield int
            yield Gt(123)
            yield from annotations

    a = AnalyzedType(MyType)
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123))

    a = AnalyzedType(Annotated[MyType, Lt(420)])
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123, lt=420))
