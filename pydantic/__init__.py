import typing

import pydantic_core
from pydantic_core.core_schema import (
    FieldSerializationInfo,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
)

from . import dataclasses
from ._internal._generate_schema import GenerateSchema as GenerateSchema
from ._migration import getattr_migration
from .annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from .config import ConfigDict
from .errors import *
from .fields import AliasChoices, AliasPath, Field, PrivateAttr, computed_field
from .functional_serializers import PlainSerializer, SerializeAsAny, WrapSerializer, field_serializer, model_serializer
from .functional_validators import (
    AfterValidator,
    BeforeValidator,
    InstanceOf,
    PlainValidator,
    SkipValidation,
    WrapValidator,
    field_validator,
    model_validator,
)
from .json_schema import WithJsonSchema
from .main import *
from .networks import *
from .type_adapter import TypeAdapter
from .types import *
from .validate_call import validate_call
from .version import VERSION
from .warnings import *

__version__ = VERSION

# this encourages pycharm to import `ValidationError` from here, not pydantic_core
ValidationError = pydantic_core.ValidationError

if typing.TYPE_CHECKING:
    # these are imported via `__getattr__` below, but we need them here for type checking and IDE support
    from .deprecated.class_validators import root_validator, validator
    from .deprecated.config import BaseConfig, Extra
    from .deprecated.tools import *
    from .root_model import RootModel

__all__ = [
    # dataclasses
    'dataclasses',
    # pydantic_core.core_schema
    'ValidationInfo',
    'ValidatorFunctionWrapHandler',
    # functional validators
    'field_validator',
    'model_validator',
    'AfterValidator',
    'BeforeValidator',
    'PlainValidator',
    'WrapValidator',
    'SkipValidation',
    'InstanceOf',
    'WithJsonSchema',
    # deprecated V1 functional validators, these are imported via `__getattr__` below
    'root_validator',
    'validator',
    # functional serializers
    'field_serializer',
    'model_serializer',
    'PlainSerializer',
    'SerializeAsAny',
    'WrapSerializer',
    'FieldSerializationInfo',
    'SerializationInfo',
    'SerializerFunctionWrapHandler',
    # config
    'ConfigDict',
    # deprecated V1 config, these are imported via `__getattr__` below
    'BaseConfig',
    'Extra',
    # validate_call
    'validate_call',
    # pydantic_core errors
    'ValidationError',
    # errors
    'PydanticErrorCodes',
    'PydanticUserError',
    'PydanticSchemaGenerationError',
    'PydanticImportError',
    'PydanticUndefinedAnnotation',
    'PydanticInvalidForJsonSchema',
    # fields
    'AliasPath',
    'AliasChoices',
    'Field',
    'computed_field',
    # main
    'BaseModel',
    'create_model',
    # network
    'AnyUrl',
    'AnyHttpUrl',
    'FileUrl',
    'HttpUrl',
    'UrlConstraints',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'CockroachDsn',
    'AmqpDsn',
    'RedisDsn',
    'MongoDsn',
    'KafkaDsn',
    'MySQLDsn',
    'MariaDBDsn',
    'validate_email',
    # root_model
    'RootModel',
    # deprecated tools, these are imported via `__getattr__` below
    'parse_obj_as',
    'schema_of',
    'schema_json_of',
    # types
    'Strict',
    'StrictStr',
    'conbytes',
    'conlist',
    'conset',
    'confrozenset',
    'constr',
    'StringConstraints',
    'ImportString',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'NonNegativeInt',
    'NonPositiveInt',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'NonNegativeFloat',
    'NonPositiveFloat',
    'FiniteFloat',
    'condecimal',
    'condate',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'FilePath',
    'DirectoryPath',
    'NewPath',
    'Json',
    'SecretStr',
    'SecretBytes',
    'StrictBool',
    'StrictBytes',
    'StrictInt',
    'StrictFloat',
    'PaymentCardNumber',
    'PrivateAttr',
    'ByteSize',
    'PastDate',
    'FutureDate',
    'PastDatetime',
    'FutureDatetime',
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    'Base64UrlBytes',
    'Base64UrlStr',
    'GetPydanticSchema',
    # type_adapter
    'TypeAdapter',
    # version
    'VERSION',
    # warnings
    'PydanticDeprecatedSince20',
    'PydanticDeprecationWarning',
    # annotated handlers
    'GetCoreSchemaHandler',
    'GetJsonSchemaHandler',
    'GenerateSchema',
]

# A mapping of {<member name>: (package, <module name>)} defining dynamic imports
_dynamic_imports: 'dict[str, tuple[str, str]]' = {
    'RootModel': (__package__, '.root_model'),
    'root_validator': (__package__, '.deprecated.class_validators'),
    'validator': (__package__, '.deprecated.class_validators'),
    'BaseConfig': (__package__, '.deprecated.config'),
    'Extra': (__package__, '.deprecated.config'),
    'parse_obj_as': (__package__, '.deprecated.tools'),
    'schema_of': (__package__, '.deprecated.tools'),
    'schema_json_of': (__package__, '.deprecated.tools'),
    # FieldValidationInfo is deprecated, and hidden behind module a `__getattr__`
    'FieldValidationInfo': ('pydantic_core', '.core_schema'),
}

_getattr_migration = getattr_migration(__name__)


def __getattr__(attr_name: str) -> object:
    dynamic_attr = _dynamic_imports.get(attr_name)
    if dynamic_attr is None:
        return _getattr_migration(attr_name)

    package, module_name = dynamic_attr

    from importlib import import_module

    module = import_module(module_name, package=package)
    return getattr(module, attr_name)
