import json
import sys
import warnings
from abc import ABCMeta
from copy import deepcopy
from enum import Enum
from functools import partial
from pathlib import Path
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    no_type_check,
)

from .class_validators import ValidatorGroup, extract_validators, inherit_validators
from .error_wrappers import ErrorWrapper, ValidationError
from .errors import ConfigError, DictError, ExtraError, MissingError
from .fields import Field
from .json import custom_pydantic_encoder, pydantic_encoder
from .parse import Protocol, load_file, load_str_bytes
from .schema import model_schema
from .types import StrBytes
from .utils import (
    AnyCallable,
    AnyType,
    ForwardRef,
    change_exception,
    resolve_annotations,
    truncate,
    validate_field_name,
)

if TYPE_CHECKING:  # pragma: no cover
    from .types import CallableGenerator
    from .class_validators import ValidatorListDict

    AnyGenerator = Generator[Any, None, None]
    TupleGenerator = Generator[Tuple[str, Any], None, None]
    DictStrAny = Dict[str, Any]
    ConfigType = Type['BaseConfig']
    DictAny = Dict[Any, Any]
    SetStr = Set[str]
    ListStr = List[str]
    Model = TypeVar('Model', bound='BaseModel')


class Extra(str, Enum):
    allow = 'allow'
    ignore = 'ignore'
    forbid = 'forbid'


class BaseConfig:
    title = None
    anystr_strip_whitespace = False
    min_anystr_length = None
    max_anystr_length = None
    validate_all = False
    extra = Extra.ignore
    allow_mutation = True
    allow_population_by_alias = False
    use_enum_values = False
    fields: Dict[str, Union[str, Dict[str, str]]] = {}
    validate_assignment = False
    error_msg_templates: Dict[str, str] = {}
    arbitrary_types_allowed = False
    json_encoders: Dict[AnyType, AnyCallable] = {}

    @classmethod
    def get_field_schema(cls, name: str) -> Dict[str, str]:
        field_config = cls.fields.get(name) or {}
        if isinstance(field_config, str):
            field_config = {'alias': field_config}
        return field_config


def inherit_config(self_config: 'ConfigType', parent_config: 'ConfigType') -> 'ConfigType':
    if not self_config:
        base_classes = (parent_config,)
    elif self_config == parent_config:
        base_classes = (self_config,)
    else:
        base_classes = self_config, parent_config  # type: ignore
    return type('Config', base_classes, {})


EXTRA_LINK = 'https://pydantic-docs.helpmanual.io/#model-config'


def set_extra(config: Type[BaseConfig], cls_name: str) -> None:
    has_ignore_extra, has_allow_extra = hasattr(config, 'ignore_extra'), hasattr(config, 'allow_extra')
    if has_ignore_extra or has_allow_extra:
        if getattr(config, 'allow_extra', False):
            config.extra = Extra.allow
        elif getattr(config, 'ignore_extra', True):
            config.extra = Extra.ignore
        else:
            config.extra = Extra.forbid

        if has_ignore_extra and has_allow_extra:
            warnings.warn(
                f'{cls_name}: "ignore_extra" and "allow_extra" are deprecated and replaced by "extra", '
                f'see {EXTRA_LINK}',
                DeprecationWarning,
            )
        elif has_ignore_extra:
            warnings.warn(
                f'{cls_name}: "ignore_extra" is deprecated and replaced by "extra", see {EXTRA_LINK}',
                DeprecationWarning,
            )
        else:
            warnings.warn(
                f'{cls_name}: "allow_extra" is deprecated and replaced by "extra", see {EXTRA_LINK}', DeprecationWarning
            )
    elif not isinstance(config.extra, Extra):
        try:
            config.extra = Extra(config.extra)
        except ValueError:
            raise ValueError(f'"{cls_name}": {config.extra} is not a valid value for "extra"')


TYPE_BLACKLIST = FunctionType, property, type, classmethod, staticmethod


class MetaModel(ABCMeta):
    @no_type_check
    def __new__(mcs, name, bases, namespace):
        fields: Dict[str, Field] = {}
        config = BaseConfig
        validators: 'ValidatorListDict' = {}
        for base in reversed(bases):
            if issubclass(base, BaseModel) and base != BaseModel:
                fields.update(deepcopy(base.__fields__))
                config = inherit_config(base.__config__, config)
                validators = inherit_validators(base.__validators__, validators)

        config = inherit_config(namespace.get('Config'), config)
        validators = inherit_validators(extract_validators(namespace), validators)
        vg = ValidatorGroup(validators)

        for f in fields.values():
            f.set_config(config)
            extra_validators = vg.get_validators(f.name)
            if extra_validators:
                f.class_validators.update(extra_validators)
                # re-run prepare to add extra validators
                f.prepare()

        set_extra(config, name)
        annotations = namespace.get('__annotations__', {})
        if sys.version_info >= (3, 7):
            annotations = resolve_annotations(annotations, namespace.get('__module__', None))

        class_vars = set()
        # annotation only fields need to come first in fields
        for ann_name, ann_type in annotations.items():
            if ann_type == ClassVar:
                class_vars.add(ann_name)
            elif not ann_name.startswith('_') and ann_name not in namespace:
                validate_field_name(bases, ann_name)
                fields[ann_name] = Field.infer(
                    name=ann_name,
                    value=...,
                    annotation=ann_type,
                    class_validators=vg.get_validators(ann_name),
                    config=config,
                )

        for var_name, value in namespace.items():
            if not var_name.startswith('_') and not isinstance(value, TYPE_BLACKLIST) and var_name not in class_vars:
                validate_field_name(bases, var_name)
                fields[var_name] = Field.infer(
                    name=var_name,
                    value=value,
                    annotation=annotations.get(var_name),
                    class_validators=vg.get_validators(var_name),
                    config=config,
                )

        vg.check_for_unused()
        if config.json_encoders:
            json_encoder = partial(custom_pydantic_encoder, config.json_encoders)
        else:
            json_encoder = pydantic_encoder
        new_namespace = {
            '__config__': config,
            '__fields__': fields,
            '__validators__': vg.validators,
            '_schema_cache': {},
            '_json_encoder': staticmethod(json_encoder),
            **{n: v for n, v in namespace.items() if n not in fields},
        }
        return super().__new__(mcs, name, bases, new_namespace)


_missing = object()


class BaseModel(metaclass=MetaModel):
    if TYPE_CHECKING:  # pragma: no cover
        # populated by the metaclass, defined here to help IDEs only
        __fields__: Dict[str, Field] = {}
        __validators__: Dict[str, AnyCallable] = {}
        __config__: Type[BaseConfig] = BaseConfig
        _json_encoder: Callable[[Any], Any] = lambda x: x
        _schema_cache: 'DictAny' = {}

    Config = BaseConfig
    __slots__ = ('__values__', '__fields_set__')

    def __init__(self, **data: Any) -> None:
        if TYPE_CHECKING:  # pragma: no cover
            self.__values__: Dict[str, Any] = {}
            self.__fields_set__: 'SetStr' = set()
        object.__setattr__(self, '__values__', self._process_values(data))
        if self.__config__.extra is Extra.allow:
            fields_set = set(data.keys())
        else:
            fields_set = data.keys() & self.__values__.keys()  # type: ignore
        object.__setattr__(self, '__fields_set__', fields_set)

    @no_type_check
    def __getattr__(self, name):
        try:
            return self.__values__[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @no_type_check
    def __setattr__(self, name, value):
        if self.__config__.extra is not Extra.allow and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        elif not self.__config__.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and does not support item assignment')
        elif self.__config__.validate_assignment:
            value_, error_ = self.fields[name].validate(value, self.dict(exclude={name}), loc=name)
            if error_:
                raise ValidationError([error_])
            else:
                self.__values__[name] = value_
                self.__fields_set__.add(name)
        else:
            self.__values__[name] = value
            self.__fields_set__.add(name)

    def __getstate__(self) -> 'DictAny':
        return {'__values__': self.__values__, '__fields_set__': self.__fields_set__}

    def __setstate__(self, state: 'DictAny') -> None:
        object.__setattr__(self, '__values__', state['__values__'])
        object.__setattr__(self, '__fields_set__', state['__fields_set__'])

    def dict(
        self, *, include: 'SetStr' = None, exclude: 'SetStr' = None, by_alias: bool = False, skip_defaults: bool = False
    ) -> 'DictStrAny':
        """
        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
        """
        get_key = self._get_key_factory(by_alias)
        get_key = partial(get_key, self.fields)

        return_keys = self._calculate_keys(include=include, exclude=exclude, skip_defaults=skip_defaults)
        if return_keys is None:
            return {get_key(k): v for k, v in self._iter(by_alias=by_alias, skip_defaults=skip_defaults)}
        else:
            return {
                get_key(k): v for k, v in self._iter(by_alias=by_alias, skip_defaults=skip_defaults) if k in return_keys
            }

    def _get_key_factory(self, by_alias: bool) -> Callable[..., str]:
        if by_alias:
            return lambda fields, key: fields[key].alias

        return lambda _, key: key

    def json(
        self,
        *,
        include: 'SetStr' = None,
        exclude: 'SetStr' = None,
        by_alias: bool = False,
        skip_defaults: bool = False,
        encoder: Optional[Callable[[Any], Any]] = None,
        **dumps_kwargs: Any,
    ) -> str:
        """
        Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

        `encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
        """
        encoder = cast(Callable[[Any], Any], encoder or self._json_encoder)
        return json.dumps(
            self.dict(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults),
            default=encoder,
            **dumps_kwargs,
        )

    @classmethod
    def parse_obj(cls: Type['Model'], obj: 'DictAny') -> 'Model':
        if not isinstance(obj, dict):
            exc = TypeError(f'{cls.__name__} expected dict not {type(obj).__name__}')
            raise ValidationError([ErrorWrapper(exc, loc='__obj__')])
        return cls(**obj)

    @classmethod
    def parse_raw(
        cls: Type['Model'],
        b: StrBytes,
        *,
        content_type: str = None,
        encoding: str = 'utf8',
        proto: Protocol = None,
        allow_pickle: bool = False,
    ) -> 'Model':
        try:
            obj = load_str_bytes(
                b, proto=proto, content_type=content_type, encoding=encoding, allow_pickle=allow_pickle
            )
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            raise ValidationError([ErrorWrapper(e, loc='__obj__')])
        return cls.parse_obj(obj)

    @classmethod
    def parse_file(
        cls: Type['Model'],
        path: Union[str, Path],
        *,
        content_type: str = None,
        encoding: str = 'utf8',
        proto: Protocol = None,
        allow_pickle: bool = False,
    ) -> 'Model':
        obj = load_file(path, proto=proto, content_type=content_type, encoding=encoding, allow_pickle=allow_pickle)
        return cls.parse_obj(obj)

    @classmethod
    def construct(cls: Type['Model'], values: 'DictAny', fields_set: 'SetStr') -> 'Model':
        """
        Creates a new model and set __values__ without any validation, thus values should already be trusted.
        Chances are you don't want to use this method directly.
        """
        m = cls.__new__(cls)
        object.__setattr__(m, '__values__', values)
        object.__setattr__(m, '__fields_set__', fields_set)
        return m

    def copy(
        self: 'Model',
        *,
        include: 'SetStr' = None,
        exclude: 'SetStr' = None,
        update: 'DictStrAny' = None,
        deep: bool = False,
    ) -> 'Model':
        """
        Duplicate a model, optionally choose which fields to include, exclude and change.

        :param include: fields to include in new model
        :param exclude: fields to exclude from new model, as with values this takes precedence over include
        :param update: values to change/add in the new model. Note: the data is not validated before creating
            the new model: you should trust this data
        :param deep: set to `True` to make a deep copy of the model
        :return: new model instance
        """
        if include is None and exclude is None and update is None:
            # skip constructing values if no arguments are passed
            v = self.__values__
        else:
            return_keys = self._calculate_keys(include=include, exclude=exclude, skip_defaults=False)
            if return_keys:
                v = {**{k: v for k, v in self.__values__.items() if k in return_keys}, **(update or {})}
            else:
                v = {**self.__values__, **(update or {})}

        if deep:
            v = deepcopy(v)
        m = self.__class__.construct(v, self.__fields_set__.copy())
        return m

    @property
    def fields(self) -> Dict[str, Field]:
        return self.__fields__

    @classmethod
    def schema(cls, by_alias: bool = True) -> 'DictStrAny':
        cached = cls._schema_cache.get(by_alias)
        if cached is not None:
            return cached
        s = model_schema(cls, by_alias=by_alias)
        cls._schema_cache[by_alias] = s
        return s

    @classmethod
    def schema_json(cls, *, by_alias: bool = True, **dumps_kwargs: Any) -> str:
        from .json import pydantic_encoder

        return json.dumps(cls.schema(by_alias=by_alias), default=pydantic_encoder, **dumps_kwargs)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls: Type['Model'], value: Union['DictStrAny', 'Model']) -> 'Model':
        if isinstance(value, dict):
            return cls(**value)
        elif isinstance(value, cls):
            return value.copy()
        else:
            with change_exception(DictError, TypeError, ValueError):
                return cls(**dict(value))  # type: ignore

    def _process_values(self, input_data: Any) -> 'DictStrAny':
        # (casting here is slow so use ignore)
        return validate_model(self, input_data)  # type: ignore

    @classmethod
    def _get_value(cls, v: Any, by_alias: bool, skip_defaults: bool) -> Any:
        if isinstance(v, BaseModel):
            return v.dict(by_alias=by_alias, skip_defaults=skip_defaults)
        elif isinstance(v, list):
            return [cls._get_value(v_, by_alias=by_alias, skip_defaults=skip_defaults) for v_ in v]
        elif isinstance(v, dict):
            return {k_: cls._get_value(v_, by_alias=by_alias, skip_defaults=skip_defaults) for k_, v_ in v.items()}
        elif isinstance(v, set):
            return {cls._get_value(v_, by_alias=by_alias, skip_defaults=skip_defaults) for v_ in v}
        elif isinstance(v, tuple):
            return tuple(cls._get_value(v_, by_alias=by_alias, skip_defaults=skip_defaults) for v_ in v)
        else:
            return v

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        """
        Try to update ForwardRefs on fields based on this Model, globalns and localns.
        """
        globalns = sys.modules[cls.__module__].__dict__
        globalns.setdefault(cls.__name__, cls)
        for f in cls.__fields__.values():
            if type(f.type_) == ForwardRef:
                f.type_ = f.type_._evaluate(globalns, localns or None)  # type: ignore
                f.prepare()

    def __iter__(self) -> 'AnyGenerator':
        """
        so `dict(model)` works
        """
        yield from self._iter()

    def _iter(self, by_alias: bool = False, skip_defaults: bool = False) -> 'TupleGenerator':
        for k, v in self.__values__.items():
            yield k, self._get_value(v, by_alias=by_alias, skip_defaults=skip_defaults)

    def _calculate_keys(
        self, include: 'SetStr' = None, exclude: Optional['SetStr'] = None, skip_defaults: bool = False
    ) -> Optional['SetStr']:

        if include is None and exclude is None and skip_defaults is False:
            return None

        if skip_defaults:
            keys = self.__fields_set__.copy()
        else:
            keys = set(self.__values__.keys())

        if include:
            keys &= include

        if exclude:
            keys -= exclude

        return keys

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseModel):
            return self.dict() == other.dict()
        else:
            return self.dict() == other

    def __repr__(self) -> str:
        return f'<{self}>'

    def to_string(self, pretty: bool = False) -> str:
        divider = '\n  ' if pretty else ' '
        return '{}{}{}'.format(
            self.__class__.__name__,
            divider,
            divider.join('{}={}'.format(k, truncate(v)) for k, v in self.__values__.items()),
        )

    def __str__(self) -> str:
        return self.to_string()

    def __dir__(self) -> 'ListStr':
        ret = list(object.__dir__(self))
        ret.extend(self.__values__.keys())
        return ret


def create_model(
    model_name: str,
    *,
    __config__: Type[BaseConfig] = None,
    __base__: Type[BaseModel] = None,
    __module__: Optional[str] = None,
    **field_definitions: Any,
) -> BaseModel:
    """
    Dynamically create a model.
    :param model_name: name of the created model
    :param __config__: config class to use for the new model
    :param __base__: base class for the new model to inherit from
    :param **field_definitions: fields of the model (or extra fields if a base is supplied) in the format
        `<name>=(<type>, <default default>)` or `<name>=<default value> eg. `foobar=(str, ...)` or `foobar=123`
    """
    if __base__:
        if __config__ is not None:
            raise ConfigError('to avoid confusion __config__ and __base__ cannot be used together')
    else:
        __base__ = BaseModel

    fields = {}
    annotations = {}

    for f_name, f_def in field_definitions.items():
        if f_name.startswith('_'):
            warnings.warn(f'fields may not start with an underscore, ignoring "{f_name}"', RuntimeWarning)
        if isinstance(f_def, tuple):
            try:
                f_annotation, f_value = f_def
            except ValueError as e:
                raise ConfigError(
                    f'field definitions should either be a tuple of (<type>, <default>) or just a '
                    f'default value, unfortunately this means tuples as '
                    f'default values are not allowed'
                ) from e
        else:
            f_annotation, f_value = None, f_def

        if f_annotation:
            annotations[f_name] = f_annotation
        fields[f_name] = f_value

    namespace: 'DictStrAny' = {'__annotations__': annotations, '__module__': __module__}
    namespace.update(fields)
    if __config__:
        namespace['Config'] = inherit_config(__config__, BaseConfig)

    return type(model_name, (__base__,), namespace)  # type: ignore


def validate_model(  # noqa: C901 (ignore complexity)
    model: Union[BaseModel, Type[BaseModel]], input_data: 'DictStrAny', raise_exc: bool = True
) -> Union['DictStrAny', Tuple['DictStrAny', Optional[ValidationError]]]:
    """
    validate data against a model.
    """
    values = {}
    errors = []
    names_used = set()
    config = model.__config__
    check_extra = config.extra is not Extra.ignore

    for name, field in model.__fields__.items():
        if type(field.type_) == ForwardRef:
            raise ConfigError(
                f'field "{field.name}" not yet prepared so type is still a ForwardRef, '
                f'you might need to call {model.__class__.__name__}.update_forward_refs().'
            )

        value = input_data.get(field.alias, _missing)
        using_name = False
        if value is _missing and config.allow_population_by_alias and field.alt_alias:
            value = input_data.get(field.name, _missing)
            using_name = True

        if value is _missing:
            if field.required:
                errors.append(ErrorWrapper(MissingError(), loc=field.alias, config=model.__config__))
                continue
            value = deepcopy(field.default)
            if not model.__config__.validate_all and not field.validate_always:
                values[name] = value
                continue
        elif check_extra:
            names_used.add(field.name if using_name else field.alias)

        v_, errors_ = field.validate(value, values, loc=field.alias, cls=model.__class__)  # type: ignore
        if isinstance(errors_, ErrorWrapper):
            errors.append(errors_)
        elif isinstance(errors_, list):
            errors.extend(errors_)
        else:
            values[name] = v_

    if check_extra:
        extra = input_data.keys() - names_used
        if extra:
            if config.extra is Extra.allow:
                for f in extra:
                    values[f] = input_data[f]
            else:
                for f in sorted(extra):
                    errors.append(ErrorWrapper(ExtraError(), loc=f, config=config))

    if not raise_exc:
        return values, ValidationError(errors) if errors else None

    if errors:
        raise ValidationError(errors)
    return values
