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
from ._migration import getattr_migration
from .colors import Color
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
    'field_validator',
    'FieldValidationInfo',
    'model_validator',
    'ValidationInfo',
    'ValidatorFunctionWrapHandler',
    # deprecated V1 functional validators
    'root_validator',
    'validator',
    # functional serializers
    'field_serializer',
    'FieldSerializationInfo',
    'model_serializer',
    'PlainSerializer',
    'SerializationInfo',
    'SerializerFunctionWrapHandler',
    'WrapSerializer',
    # config
    'BaseConfig',
    'ConfigDict',
    'Extra',
    # validate_call
    'validate_call',
    # pydantic_core errors
    'ValidationError',
    # errors
    'PydanticImportError',
    'PydanticInvalidForJsonSchema',
    'PydanticSchemaGenerationError',
    'PydanticUndefinedAnnotation',
    'PydanticUserError',
    # fields
    'AliasChoices',
    'AliasPath',
    'computed_field',
    'Field',
    # main
    'BaseModel',
    'create_model',
    'RootModel',
    # network
    'AmqpDsn',
    'AnyHttpUrl',
    'AnyUrl',
    'CockroachDsn',
    'EmailStr',
    'FileUrl',
    'HttpUrl',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'KafkaDsn',
    'MariaDBDsn',
    'MongoDsn',
    'MySQLDsn',
    'NameEmail',
    'PostgresDsn',
    'RedisDsn',
    'UrlConstraints',
    'validate_email',
    # tools
    'parse_obj_as',
    'schema_json_of',
    'schema_of',
    # types
    'AllowInfNan',
    'AwareDatetime',
    'Base64Bytes',
    'Base64Encoder',
    'Base64Str',
    'ByteSize',
    'Color'
    'conbytes',
    'condate',
    'condecimal',
    'confloat',
    'confrozenset',
    'conint',
    'conlist',
    'conset',
    'constr',
    'DirectoryPath',
    'EncodedBytes',
    'EncodedStr',
    'EncoderProtocol',
    'FilePath',
    'FiniteFloat',
    'FutureDate',
    'FutureDatetime',
    'ImportString',
    'Json',
    'NaiveDatetime',
    'NegativeFloat',
    'NegativeInt',
    'NewPath',
    'NonNegativeFloat',
    'NonNegativeInt',
    'NonPositiveFloat',
    'NonPositiveInt',
    'PastDate',
    'PastDatetime',
    'PaymentCardNumber',
    'PositiveFloat',
    'PositiveInt',
    'PrivateAttr',
    'SecretBytes',
    'SecretField',
    'SecretStr',
    'SkipValidation',
    'Strict',
    'StrictBool',
    'StrictBytes',
    'StrictFloat',
    'StrictInt',
    'StrictStr',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    # type_adapter
    'TypeAdapter',
    # version
    'VERSION',
]


__getattr__ = getattr_migration(__name__)
