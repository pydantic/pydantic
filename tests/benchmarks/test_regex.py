from typing import Annotated, Any

from pydantic import Field, create_model

from .shared import DeferredModel, rebuild_model


def test_repeated_regex_pattern(benchmark):
    ConstraintType = Annotated[str, Field(pattern='^(\\p{L}|_)(\\p{L}|\\p{N}|[.\\-_])*$')]

    fields: dict[str, Any] = {f'f{i}': ConstraintType for i in range(400)}

    TestModel = create_model('TestModel', __base__=DeferredModel, **fields)

    benchmark(rebuild_model, TestModel)
