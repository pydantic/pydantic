import dataclasses
import json
import math
import re
import sys
from collections.abc import Iterable, Iterator
from decimal import Decimal
from enum import Enum, IntEnum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    Generic,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

import pytest
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated, Literal, TypedDict, get_args, get_origin

import pydantic
from pydantic import (
    AfterValidator,
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Discriminator,
    Field,
    ImportString,
    InstanceOf,
    PlainSerializer,
    PlainValidator,
    RootModel,
    Secret,
    SerializeAsAny,
    StringConstraints,
    Tag,
    TypeAdapter,
    WrapSerializer,
    WrapValidator,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic._internal._core_utils import collect_known_metadata
from pydantic.config import JsonDict
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaValue,
    PydanticJsonSchemaWarning,
    WithJsonSchema,
    model_json_schema,
    models_json_schema,
)

T = TypeVar('T')


def test_by_alias() -> None:
    class ApplePie(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        a: float = Field(alias='b')
        b: int = Field(default=10, alias='a')

    assert ApplePie.model_json_schema() == {
        'title': 'ApplePie',
        'type': 'object',
        'properties': {'b': {'title': 'B', 'type': 'number'}, 'a': {'default': 10, 'title': 'A', 'type': 'integer'}},
        'required': ['b'],
    }