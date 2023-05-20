from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple

import dirty_equals as de
from annotated_types import Gt, Lt
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import TypeAdapter
from pydantic.annotated import GetCoreSchemaHandler
from pydantic.functional_validators import AfterValidator
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
    def __prepare_pydantic_annotations__(cls, source_type: Any, annotations: Sequence[Any]) -> Tuple[Any, List[Any]]:
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
            MetadataApplier(inner_core_schema=inner_schema, outer_core_schema=outer_schema),
            *remaining_annotations,
        ]
        return (source_type, new_annotations)


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


def test_generator_custom_type() -> None:
    class MyType(int):
        @classmethod
        def __prepare_pydantic_annotations__(
            cls, source_type: Any, annotations: Sequence[Any]
        ) -> Tuple[Any, List[Any]]:
            return (int, [Gt(123), *annotations])

    a = TypeAdapter(MyType)
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123))

    a = TypeAdapter(Annotated[MyType, Lt(420)])
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123, lt=420))
