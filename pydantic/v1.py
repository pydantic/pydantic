# NOTE This file aliases the pydantic namespace as pydantic.v1 for smoother v1 -> v2 transition
# flake8: noqa
import importlib
import os
from typing import Any

import pydantic
from pydantic import *


# allows importing of objects from modules directly
# i.e. from pydantic.v1.fields import ModelField
def __getattr__(name: str) -> Any:
    """Module level `__getattr__` to allow imports directly from the `pydantic.v1`
    namespace for all pydantic modules."""
    return getattr(pydantic, name)


# WARNING __all__ from pydantic.errors is not included here, it will be removed as an export here in v2
# please use "from pydantic.errors import ..." instead
__all__ = [
    # annotated types utils
    "create_model_from_namedtuple",
    "create_model_from_typeddict",
    # dataclasses
    "dataclasses",
    # class_validators
    "root_validator",
    "validator",
    # config
    "BaseConfig",
    "ConfigDict",
    "Extra",
    # decorator
    "validate_arguments",
    # env_settings
    "BaseSettings",
    # error_wrappers
    "ValidationError",
    # fields
    "Field",
    "Required",
    # main
    "BaseModel",
    "create_model",
    "validate_model",
    # network
    "AnyUrl",
    "AnyHttpUrl",
    "FileUrl",
    "HttpUrl",
    "stricturl",
    "EmailStr",
    "NameEmail",
    "IPvAnyAddress",
    "IPvAnyInterface",
    "IPvAnyNetwork",
    "PostgresDsn",
    "CockroachDsn",
    "AmqpDsn",
    "RedisDsn",
    "MongoDsn",
    "KafkaDsn",
    "validate_email",
    # parse
    "Protocol",
    # tools
    "parse_file_as",
    "parse_obj_as",
    "parse_raw_as",
    "schema_of",
    "schema_json_of",
    # types
    "NoneStr",
    "NoneBytes",
    "StrBytes",
    "NoneStrBytes",
    "StrictStr",
    "ConstrainedBytes",
    "conbytes",
    "ConstrainedList",
    "conlist",
    "ConstrainedSet",
    "conset",
    "ConstrainedFrozenSet",
    "confrozenset",
    "ConstrainedStr",
    "constr",
    "PyObject",
    "ConstrainedInt",
    "conint",
    "PositiveInt",
    "NegativeInt",
    "NonNegativeInt",
    "NonPositiveInt",
    "ConstrainedFloat",
    "confloat",
    "PositiveFloat",
    "NegativeFloat",
    "NonNegativeFloat",
    "NonPositiveFloat",
    "FiniteFloat",
    "ConstrainedDecimal",
    "condecimal",
    "ConstrainedDate",
    "condate",
    "UUID1",
    "UUID3",
    "UUID4",
    "UUID5",
    "FilePath",
    "DirectoryPath",
    "Json",
    "JsonWrapper",
    "SecretField",
    "SecretStr",
    "SecretBytes",
    "StrictBool",
    "StrictBytes",
    "StrictInt",
    "StrictFloat",
    "PaymentCardNumber",
    "PrivateAttr",
    "ByteSize",
    "PastDate",
    "FutureDate",
    # version
    "compiled",
    "VERSION",
]