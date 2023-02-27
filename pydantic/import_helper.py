import warnings
from importlib import import_module
from types import ModuleType
from typing import Any, Tuple


class V2MigrationRemovedException(Exception):
    ...


class V2MigrationMovedWarning(DeprecationWarning):
    ...


class V2MigrationRenamedWarning(DeprecationWarning):
    ...


class V2MigrationSuperseded(Exception):
    ...


V2_MIGRATION_MAPPING = {
    # Case: Removed
    'pydantic.Required': V2MigrationRemovedException('pydantic.Required has been removed in favour of ...'),
    'pydantic.create_model_from_namedtuple': V2MigrationRemovedException('TODO'),
    'pydantic.create_model_from_typeddict': V2MigrationRemovedException('TODO'),
    'pydantic.BaseSettings': V2MigrationRemovedException('TODO'),
    'pydantic.Protocol': V2MigrationRemovedException('TODO'),
    # __init__ __all__
    'pydantic.validate_model': V2MigrationRemovedException('TODO'),
    'pydantic.stricturl': V2MigrationRemovedException('TODO'),  # moved?
    'pydantic.parse_file_as': V2MigrationRemovedException('TODO'),
    'pydantic.parse_raw_as': V2MigrationRemovedException('TODO'),
    'pydantic.NoneStr': V2MigrationRemovedException('TODO'),
    'pydantic.NoneBytes': V2MigrationRemovedException('TODO'),
    'pydantic.StrBytes': V2MigrationRemovedException('TODO'),
    'pydantic.NoneStrBytes': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedBytes': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedList': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedSet': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedFrozenSet': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedStr': V2MigrationRemovedException('TODO'),
    'pydantic.PyObject': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedInt': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedFloat': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedDecimal': V2MigrationRemovedException('TODO'),
    'pydantic.ConstrainedDate': V2MigrationRemovedException('TODO'),
    'pydantic.JsonWrapper': V2MigrationRemovedException('TODO'),
    'pydantic.compiled': V2MigrationRemovedException('TODO'),
    # pydantic.annotated_types
    'pydantic.annotated_types.create_model_from_namedtuple': V2MigrationRemovedException('TODO'),
    'pydantic.annotated_types.create_model_from_typeddict': V2MigrationRemovedException('TODO'),
    'pydantic.annotated_types.is_legacy_typeddict': V2MigrationRemovedException('TODO'),
    # pydantic.class_validators
    'pydantic.class_validators.VALIDATOR_CONFIG_KEY': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.ROOT_VALIDATOR_CONFIG_KEY': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.ValidatorGroup': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.extract_validators': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.extract_root_validators': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.inherit_validators': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.make_generic_validator': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.prep_validators': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.all_kwargs': V2MigrationRemovedException('TODO'),
    'pydantic.class_validators.gather_all_validators': V2MigrationRemovedException('TODO'),
    # pydantic.config
    'pydantic.config.inherit_config': V2MigrationRemovedException('TODO'),
    # pydantic.datetime_parse
    'pydantic.datetime_parse.': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.date_expr': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.time_expr': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.date_re': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.time_re': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.datetime_re': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.standard_duration_re': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.iso8601_duration_re': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.EPOCH': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.MS_WATERSHED': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.MAX_NUMBER': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.StrBytesIntFloat': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.get_numeric': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.from_unix_seconds': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.parse_date': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.parse_time': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.parse_datetime': V2MigrationRemovedException('TODO'),
    'pydantic.datetime_parse.parse_duration': V2MigrationRemovedException('TODO'),
    # pydantic.env_settings
    'pydantic.env_settings.env_file_sentinel': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.SettingsSourceCallable': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.DotenvType': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.SettingsError': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.BaseSettings': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.InitSettingsSource': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.EnvSettingsSource': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.SecretsSettingsSource': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.read_env_file': V2MigrationRemovedException('TODO'),
    'pydantic.env_settings.find_case_path': V2MigrationRemovedException('TODO'),
    # pydantic.error_wrappers
    'pydantic.error_wrappers.ErrorWrapper': V2MigrationRemovedException('TODO'),
    'pydantic.error_wrappers.ErrorList': V2MigrationRemovedException('TODO'),
    'pydantic.error_wrappers.display_errors': V2MigrationRemovedException('TODO'),
    'pydantic.error_wrappers.flatten_errors': V2MigrationRemovedException('TODO'),
    'pydantic.error_wrappers.error_dict': V2MigrationRemovedException('TODO'),
    'pydantic.error_wrappers.get_exc_type': V2MigrationRemovedException('TODO'),
    # pydantic.errors
    'pydantic.errors.PydanticTypeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PydanticValueError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ConfigError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.MissingError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ExtraError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NoneIsNotAllowedError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NoneIsAllowedError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.WrongConstantError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NotNoneError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.BoolError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.BytesError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DictError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.EmailError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlSchemeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlSchemePermittedError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlUserInfoError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlHostError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlHostTldError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlPortError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UrlExtraError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.EnumError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IntEnumError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.EnumMemberError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IntegerError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.FloatError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PathError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PathNotExistsError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PathNotAFileError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PathNotADirectoryError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PyObjectError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.SequenceError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ListError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.SetError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.FrozenSetError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.TupleError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.TupleLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ListMinLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ListMaxLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ListUniqueItemsError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.SetMinLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.SetMaxLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.FrozenSetMinLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.FrozenSetMaxLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.AnyStrMinLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.AnyStrMaxLengthError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.StrError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.StrRegexError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NumberNotGtError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NumberNotGeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NumberNotLtError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NumberNotLeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NumberNotMultipleError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DecimalError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DecimalIsNotFiniteError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DecimalMaxDigitsError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DecimalMaxPlacesError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DecimalWholeDigitsError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DateTimeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DateError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DateNotInThePastError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DateNotInTheFutureError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.TimeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DurationError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.HashableError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UUIDError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.UUIDVersionError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ArbitraryTypeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ClassError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.SubclassError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.JsonError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.JsonTypeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.PatternError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.DataclassTypeError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.CallableError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPvAnyAddressError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPvAnyInterfaceError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPvAnyNetworkError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPv4AddressError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPv6AddressError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPv4NetworkError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPv6NetworkError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPv4InterfaceError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.IPv6InterfaceError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.ColorError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.StrictBoolError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.NotDigitError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.LuhnValidationError': V2MigrationRemovedException('TODO'),
    'pydantic.errors.InvalidLengthForBrand': V2MigrationRemovedException('TODO'),
    'pydantic.errors.InvalidByteSize': V2MigrationRemovedException('TODO'),
    'pydantic.errors.InvalidByteSizeUnit': V2MigrationRemovedException('TODO'),
    'pydantic.errors.MissingDiscriminator': V2MigrationRemovedException('TODO'),
    'pydantic.errors.InvalidDiscriminator': V2MigrationRemovedException('TODO'),
    # pydantic.fields
    'pydantic.fields.Required': V2MigrationRemovedException('pydantic.Required has been removed in favour of ...'),
    # 'pydantic.fields.UndefinedType': V2MigrationRemovedException('TODO'),  # Moved
    # 'pydantic.fields.Undefined': V2MigrationRemovedException('TODO'),  # Moved
    'pydantic.fields.SHAPE_SINGLETON': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_LIST': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_SET': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_MAPPING': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_TUPLE': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_TUPLE_ELLIPSIS': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_SEQUENCE': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_FROZENSET': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_ITERABLE': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_GENERIC': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_DEQUE': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_DICT': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_DEFAULTDICT': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_COUNTER': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.SHAPE_NAME_LOOKUP': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.MAPPING_LIKE_SHAPES': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.ModelField': V2MigrationMovedWarning('TODO'),
    'pydantic.fields.DeferredType': V2MigrationMovedWarning('TODO'),  # Moved
    'pydantic.fields.is_finalvar_with_default_val': V2MigrationMovedWarning('TODO'),
    # pydantic.main
    'pydantic.main.validate_custom_root_type': V2MigrationMovedWarning('TODO'),
    'pydantic.main.generate_hash_function': V2MigrationMovedWarning('TODO'),
    'pydantic.main.ANNOTATED_FIELD_UNTOUCHED_TYPES': V2MigrationMovedWarning('TODO'),
    'pydantic.main.UNTOUCHED_TYPES': V2MigrationMovedWarning('TODO'),
    'pydantic.main.validate_model': V2MigrationMovedWarning('TODO'),
    # pydantic.mypy NOTE: ERROR_ORM still exists, should it be renamed to ERROR_ATTRIBUTES
    'pydantic.mypy.BASESETTINGS_FULLNAME': V2MigrationMovedWarning('TODO'),
    'pydantic.mypy.from_orm_callback': V2MigrationMovedWarning('TODO'),  # Renamed to from_attributes_callback
    'pydantic.mypy.error_from_orm': V2MigrationMovedWarning('TODO'),  # Renamed to error_from_attributes
    # pydantic.networks
    'pydantic.networks.NetworkType': V2MigrationMovedWarning('TODO'),  # only in type checking now
    'pydantic.networks.stricturl': V2MigrationMovedWarning('TODO'),  # renamed?
    'pydantic.networks.url_regex': V2MigrationMovedWarning('TODO'),
    'pydantic.networks.multi_host_url_regex': V2MigrationMovedWarning('TODO'),
    'pydantic.networks.ascii_domain_regex': V2MigrationMovedWarning('TODO'),
    'pydantic.networks.int_domain_regex': V2MigrationMovedWarning('TODO'),
    'pydantic.networks.host_regex': V2MigrationMovedWarning('TODO'),
    'pydantic.networks.MultiHostDsn': V2MigrationMovedWarning('TODO'),
    # pydantic.parse
    'pydantic.parse.Protocol': V2MigrationRemovedException('TODO'),
    'pydantic.parse.load_str_bytes': V2MigrationMovedWarning('TODO'),
    'pydantic.parse.load_file': V2MigrationMovedWarning('TODO'),
    # pydantic.schema
    'pydantic.schema.schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.model_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_field_info_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.field_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.numeric_types': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_field_schema_validations': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_model_name_map': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_flat_models_from_model': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_flat_models_from_field': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_flat_models_from_fields': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_flat_models_from_models': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_long_model_name': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.field_type_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.model_process_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.model_type_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.enum_process_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.field_singleton_sub_fields_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.field_class_to_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.json_scheme': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.add_field_type_to_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_schema_ref': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.field_singleton_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.multitypes_literal_field_for_schema': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.encode_default': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_annotation_from_field_info': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.get_annotation_with_constraints': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.normalize_name': V2MigrationMovedWarning('TODO'),
    'pydantic.schema.SkipField': V2MigrationMovedWarning('TODO'),
    # pydantic.tools
    'pydantic.tools.parse_file_as': V2MigrationMovedWarning('TODO'),
    'pydantic.tools.parse_raw_as': V2MigrationMovedWarning('TODO'),
    # pydantic.types
    'pydantic.types.NoneStr': V2MigrationMovedWarning('TODO'),
    'pydantic.types.NoneBytes': V2MigrationMovedWarning('TODO'),
    'pydantic.types.StrBytes': V2MigrationMovedWarning('TODO'),
    'pydantic.types.NoneStrBytes': V2MigrationMovedWarning('TODO'),
    'pydantic.types.OptionalInt': V2MigrationMovedWarning('TODO'),
    'pydantic.types.OptionalIntFloat': V2MigrationMovedWarning('TODO'),
    'pydantic.types.OptionalIntFloatDecimal': V2MigrationMovedWarning('TODO'),
    'pydantic.types.OptionalDate': V2MigrationMovedWarning('TODO'),
    'pydantic.types.StrIntFloat': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedNumberMeta': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedInt': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedFloat': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedBytes': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedStr': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedSet': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedFrozenSet': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedList': V2MigrationMovedWarning('TODO'),
    'pydantic.types.PyObject': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedDecimal': V2MigrationMovedWarning('TODO'),
    'pydantic.types.FilePath': V2MigrationMovedWarning('TODO'),  # Moved to PathType??
    'pydantic.types.JsonWrapper': V2MigrationMovedWarning('TODO'),
    'pydantic.types.JsonMeta': V2MigrationMovedWarning('TODO'),
    'pydantic.types.ConstrainedDate': V2MigrationMovedWarning('TODO'),
    # pydantic.typing # TODO
    # pydantic.utils # TODO
    # pydantic.validators # TODO
    # pydantic.version
    'pydantic.version.compiled': V2MigrationMovedWarning('TODO'),
    # Case: Moved path
    'pydantic.error_wrappers.ValidationError': (
        'ValidationError has been moved from pydantic.error_wrappers during the migration to V2\n'
        'Please use either:\n'
        'from pydantic import ValidationError\n'
        'or\n'
        'from pydantic_core import ValidationError',
        'pydantic.ValidationError',
    ),
    'pydantic.class_validators.Validator': (
        'Validator has been moved from pydantic.class_validators during the migration to V2\n'
        'It is now part of the private internal API and should not be relied upon'
        'In the interim you can use at your own risk:\n'
        'from pydantic._internal._decorators import Validator',
        'pydantic._internal._decorators.Validator',
    ),
    'pydantic.class_validators.root_validator': (
        'root_validator has been moved from pydantic.class_validators during the migration to V2\n'
        'Please use either:\n'
        'from pydantic import root_validator\n'
        'or\n'
        'from pydantic.decorators import root_validator',
        'pydantic.decorators.root_validator',
    ),
    'pydantic.class_validators.validator': (
        'validator has been moved from pydantic.class_validators during the migration to V2\n'
        'Please use either:\n'
        'from pydantic import validator\n'
        'or\n'
        'from pydantic.decorators import validator',
        'pydantic.decorators.validator',
    ),
    'pydantic.utils.lenient_issubclass': (
        'lenient_issubclass has been moved from pydantic.utils during the migration to V2\n'
        'It is now part of the private internal API and should not be relied upon'
        'In the interim you can use at your own risk:\n'
        'from pydantic._internal._utils import lenient_issubclass',
        'pydantic._internal._utils.lenient_issubclass',
    )
    # Case: Renamed object
    # Case: Superseded
}


def patch_importlib_with_migration_info(importlib: ModuleType) -> None:
    __handle_fromlist = importlib._bootstrap._handle_fromlist

    def _handle_fromlist_override(
        module: ModuleType, fromlist: Tuple[str, ...], import_: Any, *, recursive: bool = False
    ) -> Any:
        inform(f"{module.__name__}.{'.'.join(fromlist)}")

        return __handle_fromlist(module, fromlist, import_, recursive=recursive)

    importlib._bootstrap._handle_fromlist = _handle_fromlist_override


def inform(object_import: str) -> Any:
    exception = V2_MIGRATION_MAPPING.get(object_import)
    if isinstance(exception, Exception):
        raise exception
    if isinstance(exception, tuple):
        warnings.warn(exception[0].strip(), V2MigrationMovedWarning)
        return import_from(exception[1])


def getattr(module_name: str, name: str) -> Any:
    obj = inform(f'{module_name}.{name}')
    if obj:
        return obj
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def import_from(object_import: str) -> Any:
    module_name, obj_name = object_import.rsplit('.', 1)
    module = import_module(module_name)
    return module.__getattribute__(obj_name)  # Needed over getattr to avoid circular imports
