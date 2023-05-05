from pydantic_core import ValidationError
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
from .config import ConfigDict, Extra
from .decorators import field_serializer, field_validator, model_serializer, model_validator, root_validator, validator
from .deprecated.config import BaseConfig
from .deprecated.tools import *
from .errors import *
from .fields import AliasChoices, AliasPath, Field, PrivateAttr, computed_field
from .main import *
from .networks import *
from .type_adapter import TypeAdapter
from .types import *
from .validate_call import validate_call
from .version import VERSION

__version__ = VERSION

# WARNING __all__ from .errors is not included here, it will be removed as an export here in v2
# please use "from pydantic.errors import ..." instead
__all__ = [
    # dataclasses
    'dataclasses',
    # decorators
    'field_validator',
    'model_validator',
    'root_validator',
    'validator',
    'field_serializer',
    'model_serializer',
    'ValidationInfo',
    'FieldValidationInfo',
    'SerializationInfo',
    'FieldSerializationInfo',
    'ValidatorFunctionWrapHandler',
    'SerializerFunctionWrapHandler',
    # config
    'BaseConfig',
    'ConfigDict',
    'Extra',
    # validate_call
    'validate_call',
    # error_wrappers
    'ValidationError',
    'PydanticUserError',
    'PydanticSchemaGenerationError',
    'PydanticImportError',
    'PydanticUndefinedAnnotation',
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
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    # type_adapter
    'TypeAdapter',
    # version
    'VERSION',
]


__getattr__ = getattr_migration(__name__)
