
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from __future__ import annotations
import os
import inspect
import weakref
from typing import IO, TYPE_CHECKING, Any, Union, TypeVar, Callable, Iterable, Optional, AsyncIterable, cast
from datetime import date, datetime
from typing_extensions import ClassVar, Protocol, TypedDict, final, override, runtime_checkable
import pydantic
from ._types import Body, Query, Headers, Timeout, NotGiven, AnyMapping, HttpxRequestFiles
from ._utils import PropertyInfo, is_list, lru_cache, is_mapping, parse_date, coerce_boolean, parse_datetime, strip_not_given, extract_type_arg, is_annotated_type, is_type_alias_type, strip_annotated_type
from ._compat import ConfigDict, GenericModel as BaseGenericModel, get_args, is_union, parse_obj, get_origin, is_literal_type, get_model_config, get_model_fields, field_get_default
_T = TypeVar('_T')

@runtime_checkable
class _ConfigProtocol(Protocol):
    allow_population_by_field_name: bool

class BaseModel(pydantic.BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra='allow', defer_build=False)

    @classmethod
    @override
    def construct(__cls: Type[ModelT], _fields_set: set[str] | None=None, **values: object) -> ModelT:
        m = __cls.__new__(__cls)
        fields_values: dict[str, object] = {}
        config = get_model_config(__cls)
        populate_by_name = config.allow_population_by_field_name if isinstance(config, _ConfigProtocol) else config.get('populate_by_name')
        if _fields_set is None:
            _fields_set = set()
        model_fields = get_model_fields(__cls)
        for name, field in model_fields.items():
            key = field.alias
            if key is None or (key not in values and populate_by_name):
                key = name
            if key in values:
                fields_values[name] = _construct_field(value=values[key], field=field, key=key)
                _fields_set.add(name)
            else:
                fields_values[name] = field_get_default(field)
        extra_field_type = _get_extra_fields_type(__cls)
        _extra = {}
        for key, value in values.items():
            if key not in model_fields:
                parsed = construct_type(value=value, type_=extra_field_type) if extra_field_type is not None else value
                _extra[key] = parsed
        object.__setattr__(m, '__dict__', fields_values)
        object.__setattr__(m, '__pydantic_private__', None)
        object.__setattr__(m, '__pydantic_extra__', _extra)
        object.__setattr__(m, '__pydantic_fields_set__', _fields_set)
        return m
    if not TYPE_CHECKING:
        model_construct = construct

def _construct_field(value: object, field: FieldInfo, key: str) -> object:
    if value is None:
        return field_get_default(field)
    type_ = field.annotation
    if type_ is None:
        raise RuntimeError(f'Unexpected field type is None for {key}')
    return construct_type(value=value, type_=type_, metadata=getattr(field, 'metadata', None))

def _get_extra_fields_type(cls: type[pydantic.BaseModel]) -> type | None:
    schema = cls.__pydantic_core_schema__
    if schema['type'] == 'model':
        fields = schema['schema']
        if fields['type'] == 'model-fields':
            extras = fields.get('extras_schema')
            if extras and 'cls' in extras:
                return extras['cls']
    return None

def is_basemodel_type(type_: type) -> TypeGuard[type[BaseModel] | type[GenericModel]]:
    origin = get_origin(type_) or type_
    if not inspect.isclass(origin):
        return False
    return issubclass(origin, BaseModel) or issubclass(origin, GenericModel)

def construct_type(*, value: object, type_: object, metadata: Optional[List[Any]]=None) -> object:
    original_type = None
    type_ = cast('type[object]', type_)
    if is_type_alias_type(type_):
        original_type = type_
        type_ = type_.__value__
    if metadata is not None and len(metadata) > 0:
        meta: tuple[Any, ...] = tuple(metadata)
    elif is_annotated_type(type_):
        meta = get_args(type_)[1:]
        type_ = extract_type_arg(type_, 0)
    else:
        meta = tuple()
    origin = get_origin(type_) or type_
    args = get_args(type_)
    if is_union(origin):
        try:
            return validate_type(type_=original_type or type_, value=value)
        except Exception:
            pass
        discriminator = _build_discriminated_union_meta(union=type_, meta_annotations=meta)
        if discriminator and is_mapping(value):
            variant_value = value.get(discriminator.field_alias_from or discriminator.field_name)
            if variant_value and isinstance(variant_value, str):
                variant_type = discriminator.mapping.get(variant_value)
                if variant_type:
                    return construct_type(type_=variant_type, value=value)
        for variant in args:
            try:
                return construct_type(value=value, type_=variant)
            except Exception:
                continue
        raise RuntimeError(f'Could not convert data into a valid instance of {type_}')
    if origin == dict:
        if not is_mapping(value):
            return value
        items_type = args[1] if len(args) > 1 else object
        return {key: construct_type(value=item, type_=items_type) for key, item in value.items()}
    if not is_literal_type(type_) and inspect.isclass(origin) and (issubclass(origin, BaseModel) or issubclass(origin, GenericModel)):
        if is_list(value):
            return [cast(Any, type_).construct(**entry) if is_mapping(entry) else entry for entry in value]
        if is_mapping(value):
            if issubclass(type_, BaseModel):
                return type_.construct(**value)
            return cast(Any, type_).construct(**value)
    if origin == list:
        if not is_list(value):
            return value
        inner_type = args[0] if args else object
        return [construct_type(value=entry, type_=inner_type) for entry in value]
    if origin == float:
        if isinstance(value, int):
            coerced = float(value)
            if coerced != value:
                return value
            return coerced
        return value
    if type_ == datetime:
        try:
            return parse_datetime(value)
        except Exception:
            return value
    if type_ == date:
        try:
            return parse_date(value)
        except Exception:
            return value
    return value
DISCRIMINATOR_CACHE: weakref.WeakKeyDictionary[type, DiscriminatorDetails] = weakref.WeakKeyDictionary()

class DiscriminatorDetails:
    field_name: str
    field_alias_from: str | None
    mapping: dict[str, type]

    def __init__(self, *, mapping: dict[str, type], discriminator_field: str, discriminator_alias: str | None) -> None:
        self.mapping = mapping
        self.field_name = discriminator_field
        self.field_alias_from = discriminator_alias

def _build_discriminated_union_meta(*, union: type, meta_annotations: tuple[Any, ...]) -> DiscriminatorDetails | None:
    try:
        cached = DISCRIMINATOR_CACHE.get(union)
    except TypeError:
        cached = None
    if cached is not None:
        return cached
    discriminator_field_name: str | None = None
    for annotation in meta_annotations:
        if isinstance(annotation, PropertyInfo) and annotation.discriminator is not None:
            discriminator_field_name = annotation.discriminator
            break
    if not discriminator_field_name:
        return None
    mapping: dict[str, type] = {}
    discriminator_alias: str | None = None
    for variant in get_args(union):
        variant = strip_annotated_type(variant)
        if is_basemodel_type(variant):
            field = _extract_field_schema_pv2(variant, discriminator_field_name)
            if not field:
                continue
            discriminator_alias = field.get('serialization_alias')
            field_schema = field['schema']
            if field_schema['type'] == 'literal':
                for entry in field_schema['expected']:
                    if isinstance(entry, str):
                        mapping[entry] = variant
    if not mapping:
        return None
    details = DiscriminatorDetails(mapping=mapping, discriminator_field=discriminator_field_name, discriminator_alias=discriminator_alias)
    try:
        DISCRIMINATOR_CACHE.setdefault(union, details)
    except TypeError:
        pass
    return details

def _extract_field_schema_pv2(model: type[BaseModel], field_name: str) -> ModelField | None:
    schema = model.__pydantic_core_schema__
    if schema['type'] == 'definitions':
        schema = schema['schema']
    if schema['type'] != 'model':
        return None
    fields_schema = schema['schema']
    if fields_schema['type'] != 'model-fields':
        return None
    field = fields_schema['fields'].get(field_name)
    if not field:
        return None
    return field

def validate_type(*, type_: type[_T], value: object) -> _T:
    if inspect.isclass(type_) and issubclass(type_, pydantic.BaseModel):
        return cast(_T, parse_obj(type_, value))
    return _validate_non_model_type(type_=type_, value=value)

class GenericModel(BaseGenericModel, BaseModel):
    pass
from pydantic import TypeAdapter as _TypeAdapter
_CachedTypeAdapter = cast('TypeAdapter[object]', lru_cache(maxsize=None)(_TypeAdapter))
TypeAdapter = _CachedTypeAdapter

def _validate_non_model_type(*, type_: type[_T], value: object) -> _T:
    return TypeAdapter(type_).validate_python(value)

class SecurityOptions(TypedDict, total=False):
    bearer_auth: bool
    admin_api_key_auth: bool

@final
class FinalRequestOptions(pydantic.BaseModel):
    method: str
    url: str
    params: Query = {}
    headers: Union[Headers, NotGiven] = NotGiven()
    max_retries: Union[int, NotGiven] = NotGiven()
    timeout: Union[float, Timeout, None, NotGiven] = NotGiven()
    files: Union[HttpxRequestFiles, None] = None
    idempotency_key: Union[str, None] = None
    post_parser: Union[Callable[[Any], Any], NotGiven] = NotGiven()
    follow_redirects: Union[bool, None] = None
    security: SecurityOptions = {'bearer_auth': True, 'admin_api_key_auth': True}
    synthesize_event_and_data: Optional[bool] = None
    content: Union[bytes, bytearray, IO[bytes], Iterable[bytes], AsyncIterable[bytes], None] = None
    json_data: Union[Body, None] = None
    extra_json: Union[AnyMapping, None] = None
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def construct(cls, _fields_set: set[str] | None=None, **values: Unpack[FinalRequestOptionsInput]) -> FinalRequestOptions:
        kwargs: dict[str, Any] = {key: strip_not_given(value) for key, value in values.items()}
        return super().model_construct(_fields_set, **kwargs)
    if not TYPE_CHECKING:
        model_construct = construct
