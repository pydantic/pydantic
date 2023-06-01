import pydantic_core
from pydantic_core.core_schema import (
    FieldSerializationInfo,
    FieldValidationInfo,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
)

from . import dataclasses
from ._internal._annotated_handlers import (
    GetCoreSchemaHandler as GetCoreSchemaHandler,
)
from ._internal._annotated_handlers import (
    GetJsonSchemaHandler as GetJsonSchemaHandler,
)
from ._migration import getattr_migration
from .config import ConfigDict, Extra
from .deprecated.class_validators import root_validator, validator
from .deprecated.config import BaseConfig  # type: ignore
from .deprecated.tools import *
from .errors import *
from .fields import AliasChoices, AliasPath, Field, PrivateAttr, computed_field
from .functional_serializers import PlainSerializer, WrapSerializer, field_serializer, model_serializer
from .functional_validators import field_validator, model_validator
from .main import *
from .networks import *
from .type_adapter import TypeAdapter
from .types import *
from .validate_call import validate_call
from .version import VERSION

__version__ = VERSION

# this encourages pycharm to import `ValidationError` from here, not pydantic_core
ValidationError = pydantic_core.ValidationError

# WARNING __all__ from .errors is not included here, it will be removed as an export here in v2
# please use "from pydantic.errors import ..." instead
__all__ = [
    # dataclasses
    'dataclasses',
    # functional validators
    'ValidationInfo',
    'FieldValidationInfo',
    'ValidatorFunctionWrapHandler',
    'field_validator',
    'model_validator',
    # deprecated V1 functional validators
    'root_validator',
    'validator',
    # functional serializers
    'field_serializer',
    'model_serializer',
    'PlainSerializer',
    'WrapSerializer',
    'FieldSerializationInfo',
    'SerializationInfo',
    'SerializerFunctionWrapHandler',
    # config
    'BaseConfig',
    'ConfigDict',
    'Extra',
    # validate_call
    'validate_call',
    # pydantic_core errors
    'ValidationError',
    # errors
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
    'RootModel',
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
    # tools
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
    'SecretField',
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
    'SkipValidation',
    'InstanceOf',
    'WithJsonSchema',
    # type_adapter
    'TypeAdapter',
    # version
    'VERSION',
    # annotated handlers
    'GetCoreSchemaHandler',
    'GetJsonSchemaHandler',
]


__getattr__ = getattr_migration(__name__)
