import warnings
from importlib import import_module
from types import ModuleType
from typing import Any, Tuple


class V2MigrationRemovedException(DeprecationWarning):
    """
    Exception raised when a user is upgrading from Pydantic V1 to V2
    and they are dependant on something that is not longer available in V2
    """


class V2MigrationMovedWarning(DeprecationWarning):
    """
    Warning raised when a user is upgrading from Pydantic V1 to V2
    and they are dependant on something that has moved location in V2
    """

    ...


class V2MigrationMovedNowPrivateWarning(DeprecationWarning):
    """
    Warning raised when a user is upgrading from Pydantic V1 to V2
    and they are dependant on something that has moved location in V2
    and is now part of the Pydantic private api so should not be relied
    upon by the user.
    """

    ...


class V2MigrationRenamedWarning(DeprecationWarning):
    """
    Warning raised when a user is upgrading from Pydantic V1 to V2
    and they are dependant on something that has been renamed in V2
    """


V2_REMOVED = {
    'pydantic.Required',
    'pydantic.create_model_from_namedtuple',
    'pydantic.create_model_from_typeddict',
    'pydantic.BaseSettings',
    'pydantic.Protocol',
    'pydantic.validate_model',
    'pydantic.stricturl',
    'pydantic.parse_file_as',
    'pydantic.parse_raw_as',
    'pydantic.NoneStr',
    'pydantic.NoneBytes',
    'pydantic.StrBytes',
    'pydantic.NoneStrBytes',
    'pydantic.ConstrainedBytes',
    'pydantic.ConstrainedList',
    'pydantic.ConstrainedSet',
    'pydantic.ConstrainedFrozenSet',
    'pydantic.ConstrainedStr',
    'pydantic.PyObject',
    'pydantic.ConstrainedInt',
    'pydantic.ConstrainedFloat',
    'pydantic.ConstrainedDecimal',
    'pydantic.ConstrainedDate',
    'pydantic.JsonWrapper',
    'pydantic.compiled',
    'pydantic.annotated_types.create_model_from_namedtuple',
    'pydantic.annotated_types.create_model_from_typeddict',
    'pydantic.annotated_types.is_legacy_typeddict',
    'pydantic.class_validators.VALIDATOR_CONFIG_KEY',
    'pydantic.class_validators.ROOT_VALIDATOR_CONFIG_KEY',
    'pydantic.class_validators.ValidatorGroup',
    'pydantic.class_validators.extract_validators',
    'pydantic.class_validators.extract_root_validators',
    'pydantic.class_validators.inherit_validators',
    'pydantic.class_validators.make_generic_validator',
    'pydantic.class_validators.prep_validators',
    'pydantic.class_validators.all_kwargs',
    'pydantic.class_validators.gather_all_validators',
    'pydantic.config.inherit_config',
    'pydantic.datetime_parse.',
    'pydantic.datetime_parse.date_expr',
    'pydantic.datetime_parse.time_expr',
    'pydantic.datetime_parse.date_re',
    'pydantic.datetime_parse.time_re',
    'pydantic.datetime_parse.datetime_re',
    'pydantic.datetime_parse.standard_duration_re',
    'pydantic.datetime_parse.iso8601_duration_re',
    'pydantic.datetime_parse.EPOCH',
    'pydantic.datetime_parse.MS_WATERSHED',
    'pydantic.datetime_parse.MAX_NUMBER',
    'pydantic.datetime_parse.StrBytesIntFloat',
    'pydantic.datetime_parse.get_numeric',
    'pydantic.datetime_parse.from_unix_seconds',
    'pydantic.datetime_parse.parse_date',
    'pydantic.datetime_parse.parse_time',
    'pydantic.datetime_parse.parse_datetime',
    'pydantic.datetime_parse.parse_duration',
    'pydantic.env_settings.env_file_sentinel',
    'pydantic.env_settings.SettingsSourceCallable',
    'pydantic.env_settings.DotenvType',
    'pydantic.env_settings.SettingsError',
    'pydantic.env_settings.BaseSettings',
    'pydantic.env_settings.InitSettingsSource',
    'pydantic.env_settings.EnvSettingsSource',
    'pydantic.env_settings.SecretsSettingsSource',
    'pydantic.env_settings.read_env_file',
    'pydantic.env_settings.find_case_path',
    'pydantic.error_wrappers.ErrorWrapper',
    'pydantic.error_wrappers.ErrorList',
    'pydantic.error_wrappers.display_errors',
    'pydantic.error_wrappers.flatten_errors',
    'pydantic.error_wrappers.error_dict',
    'pydantic.error_wrappers.get_exc_type',
    'pydantic.errors.PydanticTypeError',
    'pydantic.errors.PydanticValueError',
    'pydantic.errors.ConfigError',
    'pydantic.errors.MissingError',
    'pydantic.errors.ExtraError',
    'pydantic.errors.NoneIsNotAllowedError',
    'pydantic.errors.NoneIsAllowedError',
    'pydantic.errors.WrongConstantError',
    'pydantic.errors.NotNoneError',
    'pydantic.errors.BoolError',
    'pydantic.errors.BytesError',
    'pydantic.errors.DictError',
    'pydantic.errors.EmailError',
    'pydantic.errors.UrlError',
    'pydantic.errors.UrlSchemeError',
    'pydantic.errors.UrlSchemePermittedError',
    'pydantic.errors.UrlUserInfoError',
    'pydantic.errors.UrlHostError',
    'pydantic.errors.UrlHostTldError',
    'pydantic.errors.UrlPortError',
    'pydantic.errors.UrlExtraError',
    'pydantic.errors.EnumError',
    'pydantic.errors.IntEnumError',
    'pydantic.errors.EnumMemberError',
    'pydantic.errors.IntegerError',
    'pydantic.errors.FloatError',
    'pydantic.errors.PathError',
    'pydantic.errors.PathNotExistsError',
    'pydantic.errors.PathNotAFileError',
    'pydantic.errors.PathNotADirectoryError',
    'pydantic.errors.PyObjectError',
    'pydantic.errors.SequenceError',
    'pydantic.errors.ListError',
    'pydantic.errors.SetError',
    'pydantic.errors.FrozenSetError',
    'pydantic.errors.TupleError',
    'pydantic.errors.TupleLengthError',
    'pydantic.errors.ListMinLengthError',
    'pydantic.errors.ListMaxLengthError',
    'pydantic.errors.ListUniqueItemsError',
    'pydantic.errors.SetMinLengthError',
    'pydantic.errors.SetMaxLengthError',
    'pydantic.errors.FrozenSetMinLengthError',
    'pydantic.errors.FrozenSetMaxLengthError',
    'pydantic.errors.AnyStrMinLengthError',
    'pydantic.errors.AnyStrMaxLengthError',
    'pydantic.errors.StrError',
    'pydantic.errors.StrRegexError',
    'pydantic.errors.NumberNotGtError',
    'pydantic.errors.NumberNotGeError',
    'pydantic.errors.NumberNotLtError',
    'pydantic.errors.NumberNotLeError',
    'pydantic.errors.NumberNotMultipleError',
    'pydantic.errors.DecimalError',
    'pydantic.errors.DecimalIsNotFiniteError',
    'pydantic.errors.DecimalMaxDigitsError',
    'pydantic.errors.DecimalMaxPlacesError',
    'pydantic.errors.DecimalWholeDigitsError',
    'pydantic.errors.DateTimeError',
    'pydantic.errors.DateError',
    'pydantic.errors.DateNotInThePastError',
    'pydantic.errors.DateNotInTheFutureError',
    'pydantic.errors.TimeError',
    'pydantic.errors.DurationError',
    'pydantic.errors.HashableError',
    'pydantic.errors.UUIDError',
    'pydantic.errors.UUIDVersionError',
    'pydantic.errors.ArbitraryTypeError',
    'pydantic.errors.ClassError',
    'pydantic.errors.SubclassError',
    'pydantic.errors.JsonError',
    'pydantic.errors.JsonTypeError',
    'pydantic.errors.PatternError',
    'pydantic.errors.DataclassTypeError',
    'pydantic.errors.CallableError',
    'pydantic.errors.IPvAnyAddressError',
    'pydantic.errors.IPvAnyInterfaceError',
    'pydantic.errors.IPvAnyNetworkError',
    'pydantic.errors.IPv4AddressError',
    'pydantic.errors.IPv6AddressError',
    'pydantic.errors.IPv4NetworkError',
    'pydantic.errors.IPv6NetworkError',
    'pydantic.errors.IPv4InterfaceError',
    'pydantic.errors.IPv6InterfaceError',
    'pydantic.errors.ColorError',
    'pydantic.errors.StrictBoolError',
    'pydantic.errors.NotDigitError',
    'pydantic.errors.LuhnValidationError',
    'pydantic.errors.InvalidLengthForBrand',
    'pydantic.errors.InvalidByteSize',
    'pydantic.errors.InvalidByteSizeUnit',
    'pydantic.errors.MissingDiscriminator',
    'pydantic.errors.InvalidDiscriminator',
    'pydantic.fields.Required',
    'pydantic.parse.Protocol',
}

V2_MOVED = {
    'pydantic.fields.SHAPE_SINGLETON': {'v2_path': ''},
    'pydantic.fields.SHAPE_LIST': {'v2_path': ''},
    'pydantic.fields.SHAPE_SET': {'v2_path': ''},
    'pydantic.fields.SHAPE_MAPPING': {'v2_path': ''},
    'pydantic.fields.SHAPE_TUPLE': {'v2_path': ''},
    'pydantic.fields.SHAPE_TUPLE_ELLIPSIS': {'v2_path': ''},
    'pydantic.fields.SHAPE_SEQUENCE': {'v2_path': ''},
    'pydantic.fields.SHAPE_FROZENSET': {'v2_path': ''},
    'pydantic.fields.SHAPE_ITERABLE': {'v2_path': ''},
    'pydantic.fields.SHAPE_GENERIC': {'v2_path': ''},
    'pydantic.fields.SHAPE_DEQUE': {'v2_path': ''},
    'pydantic.fields.SHAPE_DICT': {'v2_path': ''},
    'pydantic.fields.SHAPE_DEFAULTDICT': {'v2_path': ''},
    'pydantic.fields.SHAPE_COUNTER': {'v2_path': ''},
    'pydantic.fields.SHAPE_NAME_LOOKUP': {'v2_path': ''},
    'pydantic.fields.MAPPING_LIKE_SHAPES': {'v2_path': ''},
    'pydantic.fields.ModelField': {'v2_path': ''},
    'pydantic.fields.DeferredType': {'v2_path': ''},
    'pydantic.fields.is_finalvar_with_default_val': {'v2_path': ''},
    'pydantic.main.validate_custom_root_type': {'v2_path': ''},
    'pydantic.main.generate_hash_function': {'v2_path': ''},
    'pydantic.main.ANNOTATED_FIELD_UNTOUCHED_TYPES': {'v2_path': ''},
    'pydantic.main.UNTOUCHED_TYPES': {'v2_path': ''},
    'pydantic.main.validate_model': {'v2_path': ''},
    'pydantic.mypy.BASESETTINGS_FULLNAME': {'v2_path': ''},
    'pydantic.mypy.from_orm_callback': {'v2_path': ''},
    'pydantic.mypy.error_from_orm': {'v2_path': ''},
    'pydantic.networks.NetworkType': {'v2_path': ''},
    'pydantic.networks.stricturl': {'v2_path': ''},
    'pydantic.networks.url_regex': {'v2_path': ''},
    'pydantic.networks.multi_host_url_regex': {'v2_path': ''},
    'pydantic.networks.ascii_domain_regex': {'v2_path': ''},
    'pydantic.networks.int_domain_regex': {'v2_path': ''},
    'pydantic.networks.host_regex': {'v2_path': ''},
    'pydantic.networks.MultiHostDsn': {'v2_path': ''},
    'pydantic.parse.load_str_bytes': {'v2_path': ''},
    'pydantic.parse.load_file': {'v2_path': ''},
    'pydantic.schema.schema': {'v2_path': ''},
    'pydantic.schema.model_schema': {'v2_path': ''},
    'pydantic.schema.get_field_info_schema': {'v2_path': ''},
    'pydantic.schema.field_schema': {'v2_path': ''},
    'pydantic.schema.numeric_types': {'v2_path': ''},
    'pydantic.schema.get_field_schema_validations': {'v2_path': ''},
    'pydantic.schema.get_model_name_map': {'v2_path': ''},
    'pydantic.schema.get_flat_models_from_model': {'v2_path': ''},
    'pydantic.schema.get_flat_models_from_field': {'v2_path': ''},
    'pydantic.schema.get_flat_models_from_fields': {'v2_path': ''},
    'pydantic.schema.get_flat_models_from_models': {'v2_path': ''},
    'pydantic.schema.get_long_model_name': {'v2_path': ''},
    'pydantic.schema.field_type_schema': {'v2_path': ''},
    'pydantic.schema.model_process_schema': {'v2_path': ''},
    'pydantic.schema.model_type_schema': {'v2_path': ''},
    'pydantic.schema.enum_process_schema': {'v2_path': ''},
    'pydantic.schema.field_singleton_sub_fields_schema': {'v2_path': ''},
    'pydantic.schema.field_class_to_schema': {'v2_path': ''},
    'pydantic.schema.json_scheme': {'v2_path': ''},
    'pydantic.schema.add_field_type_to_schema': {'v2_path': ''},
    'pydantic.schema.get_schema_ref': {'v2_path': ''},
    'pydantic.schema.field_singleton_schema': {'v2_path': ''},
    'pydantic.schema.multitypes_literal_field_for_schema': {'v2_path': ''},
    'pydantic.schema.encode_default': {'v2_path': ''},
    'pydantic.schema.get_annotation_from_field_info': {'v2_path': ''},
    'pydantic.schema.get_annotation_with_constraints': {'v2_path': ''},
    'pydantic.schema.normalize_name': {'v2_path': ''},
    'pydantic.schema.SkipField': {'v2_path': ''},
    'pydantic.tools.parse_file_as': {'v2_path': ''},
    'pydantic.tools.parse_raw_as': {'v2_path': ''},
    'pydantic.types.NoneStr': {'v2_path': ''},
    'pydantic.types.NoneBytes': {'v2_path': ''},
    'pydantic.types.StrBytes': {'v2_path': ''},
    'pydantic.types.NoneStrBytes': {'v2_path': ''},
    'pydantic.types.OptionalInt': {'v2_path': ''},
    'pydantic.types.OptionalIntFloat': {'v2_path': ''},
    'pydantic.types.OptionalIntFloatDecimal': {'v2_path': ''},
    'pydantic.types.OptionalDate': {'v2_path': ''},
    'pydantic.types.StrIntFloat': {'v2_path': ''},
    'pydantic.types.ConstrainedNumberMeta': {'v2_path': ''},
    'pydantic.types.ConstrainedInt': {'v2_path': ''},
    'pydantic.types.ConstrainedFloat': {'v2_path': ''},
    'pydantic.types.ConstrainedBytes': {'v2_path': ''},
    'pydantic.types.ConstrainedStr': {'v2_path': ''},
    'pydantic.types.ConstrainedSet': {'v2_path': ''},
    'pydantic.types.ConstrainedFrozenSet': {'v2_path': ''},
    'pydantic.types.ConstrainedList': {'v2_path': ''},
    'pydantic.types.PyObject': {'v2_path': ''},
    'pydantic.types.ConstrainedDecimal': {'v2_path': ''},
    'pydantic.types.FilePath': {'v2_path': ''},
    'pydantic.types.JsonWrapper': {'v2_path': ''},
    'pydantic.types.JsonMeta': {'v2_path': ''},
    'pydantic.types.ConstrainedDate': {'v2_path': ''},
    'pydantic.version.compiled': {'v2_path': ''},
    'pydantic.error_wrappers.ValidationError': {
        'v2_path': 'pydantic.ValidationError',
        'extra': 'Please use either:\n'
        'from pydantic import ValidationError\n'
        'or\n'
        'from pydantic_core import ValidationError',
    },
    'pydantic.class_validators.Validator': {
        'v2_path': 'pydantic._internal._decorators.Validator',
        'extra': 'In the interim you can use at your own risk:\n'
        'from pydantic._internal._decorators import Validator',
    },
    'pydantic.class_validators.root_validator': {
        'v2_path': 'pydantic.decorators.root_validator',
        'extra': 'Please use either:\n'
        'from pydantic import root_validator\n'
        'or\n'
        'from pydantic.decorators import root_validator',
    },
    'pydantic.class_validators.validator': {
        'v2_path': 'pydantic.decorators.validator',
        'extra': 'Please use either:\nfrom pydantic import validator\n'
        'or\n'
        'from pydantic.decorators import validator',
    },
    'pydantic.utils.lenient_issubclass': {
        'v2_path': 'pydantic._internal._utils.lenient_issubclass',
        'extra': 'In the interim you can use at your own risk:\n'
        'from pydantic._internal._utils import lenient_issubclass',
    },
    'pydantic.mypy.ERROR_ORM': {'v2_path': 'pydantic.mypy.ERROR_ATTRIBUTES'},  # NOTE: This one is renamed not "moved"
}

# TODO: Need to go through the git diff from v1 -> v2 for moved/removed
# pydantic.typing
# pydantic.utils
# pydantic.validators


def patch_importlib_with_migration_info(importlib: ModuleType) -> None:
    __handle_fromlist = importlib._bootstrap._handle_fromlist

    def _handle_fromlist_override(
        module: ModuleType, fromlist: Tuple[str, ...], import_: Any, *, recursive: bool = False
    ) -> Any:
        inform(f"{module.__name__}.{'.'.join(fromlist)}")

        return __handle_fromlist(module, fromlist, import_, recursive=recursive)

    importlib._bootstrap._handle_fromlist = _handle_fromlist_override


def inform(object_import: str) -> Any:
    if object_import in V2_REMOVED:
        raise V2MigrationRemovedException(f'{object_import} has removed during the migration from V1 to V2')
    moved = V2_MOVED.get(object_import)
    if moved:
        is_now_private = any(part.startswith('_') for part in moved['v2_path'].split('.'))
        message = f"{object_import} has been moved to {moved['v2_path']} during the migration from V1 to V2\n"
        if is_now_private:
            warnings.warn(
                f"{message}{moved['v2_path']} is now part of the private internal API"
                f" and should not be relied upon{moved.get('extra', '')}",
                V2MigrationMovedNowPrivateWarning,
            )
        else:
            warnings.warn(f"{message}{moved.get('extra', '')}", V2MigrationMovedWarning)

        return import_from(moved['v2_path'])


def getattr(module_name: str, name: str) -> Any:
    obj = inform(f'{module_name}.{name}')
    if obj:
        return obj
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def import_from(object_import: str) -> Any:
    module_name, obj_name = object_import.rsplit('.', 1)
    module = import_module(module_name)
    return module.__getattribute__(obj_name)  # Needed over getattr to avoid circular imports
