from dataclasses import dataclass
from typing import Annotated, Any, List, Sequence

from annotated_types import Gt
from pydantic_core import CoreSchema, core_schema

from pydantic.analyzed_type import AnalyzedType
from pydantic.annotated import GetCoreSchemaHandler
from pydantic.annotated_arguments import AfterValidator
from pydantic.json_schema import GetJsonSchemaHandler, JsonSchemaValue


def test_prepare_annotations_decimal_like() -> None:
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
                MetadataApplier(inner_core_schema=inner_schema, outer_core_schema=outer_schema),
                *remaining_annotations,
            ]
            return new_annotations

    def no_op_val(x: Any) -> Any:
        return x

    a = AnalyzedType(List[Annotated[MyDecimal, Gt(10), AfterValidator(no_op_val)]])

    assert a.core_schema == core_schema.list_schema(
        core_schema.no_info_after_validator_function(
            no_op_val, core_schema.no_info_after_validator_function(MyDecimal, core_schema.float_schema(gt=10))
        )
    )
