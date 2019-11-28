import json
import sys
import warnings
from abc import ABCMeta
from copy import deepcopy
from enum import Enum
from functools import partial
from pathlib import Path
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast, no_type_check

from .class_validators import ROOT_KEY, ValidatorGroup, extract_root_validators, extract_validators, inherit_validators
from .error_wrappers import ErrorWrapper, ValidationError
from .errors import ConfigError, DictError, ExtraError, MissingError
from .fields import SHAPE_MAPPING, ModelField, Undefined
from .json import custom_pydantic_encoder, pydantic_encoder
from .parse import Protocol, load_file, load_str_bytes
from .schema import model_schema
from .types import PyObject, StrBytes
from .typing import AnyCallable, AnyType, ForwardRef, is_classvar, resolve_annotations, update_field_forward_refs
from .utils import GetterDict, Representation, ValueItems, lenient_issubclass, validate_field_name

if TYPE_CHECKING:
    from .class_validators import ValidatorListDict
    from .types import ModelOrDc
    from .typing import CallableGenerator, TupleGenerator, DictStrAny, DictAny, SetStr
    from .typing import AbstractSetIntStr, DictIntStrAny, ReprArgs  # noqa: F401

    ConfigType = Type['BaseConfig']
    Model = TypeVar('Model', bound='BaseModel')

try:
    import cython  # type: ignore
except ImportError:
    compiled: bool = False
else:  # pragma: no cover
    try:
        compiled = cython.compiled
    except AttributeError:
        compiled = False

__all__ = 'BaseConfig', 'BaseModel', 'Extra', 'compiled', 'create_model', 'validate_model'


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
    allow_population_by_field_name = False
    use_enum_values = False
    fields: Dict[str, Union[str, Dict[str, str]]] = {}
    validate_assignment = False
    error_msg_templates: Dict[str, str] = {}
    arbitrary_types_allowed = False
    orm_mode: bool = False
    getter_dict: Type[GetterDict] = GetterDict
    alias_generator: Optional[Callable[[str], str]] = None
    keep_untouched: Tuple[type, ...] = ()
    schema_extra: Dict[str, Any] = {}
    json_loads: Callable[[str], Any] = json.loads
    json_dumps: Callable[..., str] = json.dumps
    json_encoders: Dict[AnyType, AnyCallable] = {}

    @classmethod
    def get_field_info(cls, name: str) -> Dict[str, Any]:
        field_info = cls.fields.get(name) or {}
        if isinstance(field_info, str):
            field_info = {'alias': field_info}
        elif cls.alias_generator and 'alias' not in field_info:
            alias = cls.alias_generator(name)
            if not isinstance(alias, str):
                raise TypeError(f'Config.alias_generator must return str, not {type(alias)}')
            field_info['alias'] = alias
        return field_info

    @classmethod
    def prepare_field(cls, field: 'ModelField') -> None:
        """
        Optional hook to check or modify fields during model creation.
        """
        pass


def inherit_config(self_config: 'ConfigType', parent_config: 'ConfigType') -> 'ConfigType':
    if not self_config:
        base_classes = (parent_config,)
    elif self_config == parent_config:
        base_classes = (self_config,)
    else:
        base_classes = self_config, parent_config  # type: ignore
    return type('Config', base_classes, {})


EXTRA_LINK = 'https://pydantic-docs.helpmanual.io/usage/model_config/'


def prepare_config(config: Type[BaseConfig], cls_name: str) -> None:
    if not isinstance(config.extra, Extra):
        try:
            config.extra = Extra(config.extra)
        except ValueError:
            raise ValueError(f'"{cls_name}": {config.extra} is not a valid value for "extra"')

    if hasattr(config, 'allow_population_by_alias'):
        warnings.warn(
            f'{cls_name}: "allow_population_by_alias" is deprecated and replaced by "allow_population_by_field_name"',
            DeprecationWarning,
        )
        config.allow_population_by_field_name = config.allow_population_by_alias  # type: ignore

    if hasattr(config, 'case_insensitive') and any('BaseSettings.Config' in c.__qualname__ for c in config.__mro__):
        warnings.warn(
            f'{cls_name}: "case_insensitive" is deprecated on BaseSettings config and replaced by '
            f'"case_sensitive" (default False)',
            DeprecationWarning,
        )
        config.case_sensitive = not config.case_insensitive  # type: ignore


def is_valid_field(name: str) -> bool:
    if not name.startswith('_'):
        return True
    return ROOT_KEY == name


def validate_custom_root_type(fields: Dict[str, ModelField]) -> None:
    if len(fields) > 1:
        raise ValueError('__root__ cannot be mixed with other fields')


UNTOUCHED_TYPES = FunctionType, property, type, classmethod, staticmethod


class ModelMetaclass(ABCMeta):
    @no_type_check  # noqa C901
    def __new__(mcs, name, bases, namespace, **kwargs):  # noqa C901
        fields: Dict[str, ModelField] = {}
        config = BaseConfig
        validators: 'ValidatorListDict' = {}
        pre_root_validators, post_root_validators = [], []
        for base in reversed(bases):
            if issubclass(base, BaseModel) and base != BaseModel:
                fields.update(deepcopy(base.__fields__))
                config = inherit_config(base.__config__, config)
                validators = inherit_validators(base.__validators__, validators)
                pre_root_validators += base.__pre_root_validators__
                post_root_validators += base.__post_root_validators__

        config = inherit_config(namespace.get('Config'), config)
        validators = inherit_validators(extract_validators(namespace), validators)
        vg = ValidatorGroup(validators)

        for f in fields.values():
            f.set_config(config)
            extra_validators = vg.get_validators(f.name)
            if extra_validators:
                f.class_validators.update(extra_validators)
                # re-run prepare to add extra validators
                f.populate_validators()

        prepare_config(config, name)

        class_vars = set()
        if (namespace.get('__module__'), namespace.get('__qualname__')) != ('pydantic.main', 'BaseModel'):
            annotations = resolve_annotations(namespace.get('__annotations__', {}), namespace.get('__module__', None))
            untouched_types = UNTOUCHED_TYPES + config.keep_untouched
            # annotation only fields need to come first in fields
            for ann_name, ann_type in annotations.items():
                if is_classvar(ann_type):
                    class_vars.add(ann_name)
                elif is_valid_field(ann_name):
                    validate_field_name(bases, ann_name)
                    value = namespace.get(ann_name, Undefined)
                    if (
                        isinstance(value, untouched_types)
                        and ann_type != PyObject
                        and not lenient_issubclass(getattr(ann_type, '__origin__', None), Type)
                    ):
                        continue
                    fields[ann_name] = ModelField.infer(
                        name=ann_name,
                        value=value,
                        annotation=ann_type,
                        class_validators=vg.get_validators(ann_name),
                        config=config,
                    )

            for var_name, value in namespace.items():
                if (
                    var_name not in annotations
                    and is_valid_field(var_name)
                    and not isinstance(value, untouched_types)
                    and var_name not in class_vars
                ):
                    validate_field_name(bases, var_name)
                    inferred = ModelField.infer(
                        name=var_name,
                        value=value,
                        annotation=annotations.get(var_name),
                        class_validators=vg.get_validators(var_name),
                        config=config,
                    )
                    if var_name in fields and inferred.type_ != fields[var_name].type_:
                        raise TypeError(
                            f'The type of {name}.{var_name} differs from the new default value; '
                            f'if you wish to change the type of this field, please use a type annotation'
                        )
                    fields[var_name] = inferred

        _custom_root_type = ROOT_KEY in fields
        if _custom_root_type:
            validate_custom_root_type(fields)
        vg.check_for_unused()
        if config.json_encoders:
            json_encoder = partial(custom_pydantic_encoder, config.json_encoders)
        else:
            json_encoder = pydantic_encoder
        pre_rv_new, post_rv_new = extract_root_validators(namespace)
        new_namespace = {
            '__config__': config,
            '__fields__': fields,
            '__field_defaults__': {n: f.default for n, f in fields.items() if not f.required},
            '__validators__': vg.validators,
            '__pre_root_validators__': pre_root_validators + pre_rv_new,
            '__post_root_validators__': post_root_validators + post_rv_new,
            '__schema_cache__': {},
            '__json_encoder__': staticmethod(json_encoder),
            '__custom_root_type__': _custom_root_type,
            **{n: v for n, v in namespace.items() if n not in fields},
        }
        return super().__new__(mcs, name, bases, new_namespace, **kwargs)


class BaseModel(metaclass=ModelMetaclass):
    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __fields__: Dict[str, ModelField] = {}
        __field_defaults__: Dict[str, Any] = {}
        __validators__: Dict[str, AnyCallable] = {}
        __pre_root_validators__: List[AnyCallable]
        __post_root_validators__: List[AnyCallable]
        __config__: Type[BaseConfig] = BaseConfig
        __root__: Any = None
        __json_encoder__: Callable[[Any], Any] = lambda x: x
        __schema_cache__: 'DictAny' = {}
        __custom_root_type__: bool = False

    Config = BaseConfig
    __slots__ = ('__dict__', '__fields_set__')
    # equivalent of inheriting from Representation
    __repr_name__ = Representation.__repr_name__
    __repr_str__ = Representation.__repr_str__
    __pretty__ = Representation.__pretty__
    __str__ = Representation.__str__
    __repr__ = Representation.__repr__

    def __init__(__pydantic_self__, **data: Any) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        if TYPE_CHECKING:
            __pydantic_self__.__dict__: Dict[str, Any] = {}
            __pydantic_self__.__fields_set__: 'SetStr' = set()
        values, fields_set, validation_error = validate_model(__pydantic_self__.__class__, data)
        if validation_error:
            raise validation_error
        object.__setattr__(__pydantic_self__, '__dict__', values)
        object.__setattr__(__pydantic_self__, '__fields_set__', fields_set)

    @no_type_check
    def __setattr__(self, name, value):
        if self.__config__.extra is not Extra.allow and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        elif not self.__config__.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and does not support item assignment')
        elif self.__config__.validate_assignment:
            known_field = self.__fields__.get(name, None)
            if known_field:
                value, error_ = known_field.validate(value, self.dict(exclude={name}), loc=name)
                if error_:
                    raise ValidationError([error_], type(self))
        self.__dict__[name] = value
        self.__fields_set__.add(name)

    def __getstate__(self) -> 'DictAny':
        return {'__dict__': self.__dict__, '__fields_set__': self.__fields_set__}

    def __setstate__(self, state: 'DictAny') -> None:
        object.__setattr__(self, '__dict__', state['__dict__'])
        object.__setattr__(self, '__fields_set__', state['__fields_set__'])

    def dict(
        self,
        *,
        include: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> 'DictStrAny':
        """
        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
        """
        if skip_defaults is not None:
            warnings.warn(
                f'{self.__class__.__name__}.dict(): "skip_defaults" is deprecated and replaced by "exclude_unset"',
                DeprecationWarning,
            )
            exclude_unset = skip_defaults
        get_key = self._get_key_factory(by_alias)
        get_key = partial(get_key, self.__fields__)

        allowed_keys = self._calculate_keys(include=include, exclude=exclude, exclude_unset=exclude_unset)
        return {
            get_key(k): v
            for k, v in self._iter(
                to_dict=True,
                by_alias=by_alias,
                allowed_keys=allowed_keys,
                include=include,
                exclude=exclude,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        }

    def _get_key_factory(self, by_alias: bool) -> Callable[..., str]:
        if by_alias:
            return lambda fields, key: fields[key].alias if key in fields else key

        return lambda _, key: key

    def json(
        self,
        *,
        include: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        encoder: Optional[Callable[[Any], Any]] = None,
        **dumps_kwargs: Any,
    ) -> str:
        """
        Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

        `encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
        """
        if skip_defaults is not None:
            warnings.warn(
                f'{self.__class__.__name__}.json(): "skip_defaults" is deprecated and replaced by "exclude_unset"',
                DeprecationWarning,
            )
            exclude_unset = skip_defaults
        encoder = cast(Callable[[Any], Any], encoder or self.__json_encoder__)
        data = self.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if self.__custom_root_type__:
            data = data[ROOT_KEY]
        return self.__config__.json_dumps(data, default=encoder, **dumps_kwargs)

    @classmethod
    def parse_obj(cls: Type['Model'], obj: Any) -> 'Model':
        if cls.__custom_root_type__ and (
            not (isinstance(obj, dict) and obj.keys() == {ROOT_KEY}) or cls.__fields__[ROOT_KEY].shape == SHAPE_MAPPING
        ):
            obj = {ROOT_KEY: obj}
        elif not isinstance(obj, dict):
            try:
                obj = dict(obj)
            except (TypeError, ValueError) as e:
                exc = TypeError(f'{cls.__name__} expected dict not {type(obj).__name__}')
                raise ValidationError([ErrorWrapper(exc, loc=ROOT_KEY)], cls) from e
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
                b,
                proto=proto,
                content_type=content_type,
                encoding=encoding,
                allow_pickle=allow_pickle,
                json_loads=cls.__config__.json_loads,
            )
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            raise ValidationError([ErrorWrapper(e, loc=ROOT_KEY)], cls)
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
    def from_orm(cls: Type['Model'], obj: Any) -> 'Model':
        if not cls.__config__.orm_mode:
            raise ConfigError('You must have the config attribute orm_mode=True to use from_orm')
        obj = cls._decompose_class(obj)
        m = cls.__new__(cls)
        values, fields_set, validation_error = validate_model(cls, obj)
        if validation_error:
            raise validation_error
        object.__setattr__(m, '__dict__', values)
        object.__setattr__(m, '__fields_set__', fields_set)
        return m

    @classmethod
    def construct(cls: Type['Model'], _fields_set: Optional['SetStr'] = None, **values: Any) -> 'Model':
        """
        Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
        Default values are respected, but no other validation is performed.
        """
        m = cls.__new__(cls)
        object.__setattr__(m, '__dict__', {**deepcopy(cls.__field_defaults__), **values})
        if _fields_set is None:
            _fields_set = set(values.keys())
        object.__setattr__(m, '__fields_set__', _fields_set)
        return m

    def copy(
        self: 'Model',
        *,
        include: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
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
            v = self.__dict__
        else:
            allowed_keys = self._calculate_keys(include=include, exclude=exclude, exclude_unset=False, update=update)
            if allowed_keys is None:
                v = {**self.__dict__, **(update or {})}
            else:
                v = {
                    **dict(
                        self._iter(
                            to_dict=False,
                            by_alias=False,
                            include=include,
                            exclude=exclude,
                            exclude_unset=False,
                            allowed_keys=allowed_keys,
                        )
                    ),
                    **(update or {}),
                }

        if deep:
            v = deepcopy(v)

        cls = self.__class__
        m = cls.__new__(cls)
        object.__setattr__(m, '__dict__', v)
        object.__setattr__(m, '__fields_set__', self.__fields_set__.copy())
        return m

    @classmethod
    def schema(cls, by_alias: bool = True) -> 'DictStrAny':
        cached = cls.__schema_cache__.get(by_alias)
        if cached is not None:
            return cached
        s = model_schema(cls, by_alias=by_alias)
        cls.__schema_cache__[by_alias] = s
        return s

    @classmethod
    def schema_json(cls, *, by_alias: bool = True, **dumps_kwargs: Any) -> str:
        from .json import pydantic_encoder

        return cls.__config__.json_dumps(cls.schema(by_alias=by_alias), default=pydantic_encoder, **dumps_kwargs)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls: Type['Model'], value: Any) -> 'Model':
        if isinstance(value, dict):
            return cls(**value)
        elif isinstance(value, cls):
            return value.copy()
        elif cls.__config__.orm_mode:
            return cls.from_orm(value)
        else:
            try:
                value_as_dict = dict(value)
            except (TypeError, ValueError) as e:
                raise DictError() from e
            return cls(**value_as_dict)

    @classmethod
    def _decompose_class(cls: Type['Model'], obj: Any) -> GetterDict:
        return cls.__config__.getter_dict(obj)

    @classmethod
    @no_type_check
    def _get_value(
        cls,
        v: Any,
        to_dict: bool,
        by_alias: bool,
        include: Optional[Union['AbstractSetIntStr', 'DictIntStrAny']],
        exclude: Optional[Union['AbstractSetIntStr', 'DictIntStrAny']],
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
    ) -> Any:

        if isinstance(v, BaseModel):
            if to_dict:
                return v.dict(
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    include=include,
                    exclude=exclude,
                    exclude_none=exclude_none,
                )
            else:
                return v.copy(include=include, exclude=exclude)

        value_exclude = ValueItems(v, exclude) if exclude else None
        value_include = ValueItems(v, include) if include else None

        if isinstance(v, dict):
            return {
                k_: cls._get_value(
                    v_,
                    to_dict=to_dict,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    include=value_include and value_include.for_element(k_),
                    exclude=value_exclude and value_exclude.for_element(k_),
                    exclude_none=exclude_none,
                )
                for k_, v_ in v.items()
                if (not value_exclude or not value_exclude.is_excluded(k_))
                and (not value_include or value_include.is_included(k_))
            }

        elif isinstance(v, (list, set, tuple)):
            return type(v)(
                cls._get_value(
                    v_,
                    to_dict=to_dict,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    include=value_include and value_include.for_element(i),
                    exclude=value_exclude and value_exclude.for_element(i),
                    exclude_none=exclude_none,
                )
                for i, v_ in enumerate(v)
                if (not value_exclude or not value_exclude.is_excluded(i))
                and (not value_include or value_include.is_included(i))
            )

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
            update_field_forward_refs(f, globalns=globalns, localns=localns)

    def __iter__(self) -> 'TupleGenerator':
        """
        so `dict(model)` works
        """
        yield from self._iter()

    def _iter(
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        allowed_keys: Optional['SetStr'] = None,
        include: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> 'TupleGenerator':

        value_exclude = ValueItems(self, exclude) if exclude else None
        value_include = ValueItems(self, include) if include else None

        if exclude_defaults:
            if allowed_keys is None:
                allowed_keys = set(self.__fields__)
            for k, v in self.__field_defaults__.items():
                if self.__dict__[k] == v:
                    allowed_keys.discard(k)

        for k, v in self.__dict__.items():
            if allowed_keys is None or k in allowed_keys:
                value = self._get_value(
                    v,
                    to_dict=to_dict,
                    by_alias=by_alias,
                    include=value_include and value_include.for_element(k),
                    exclude=value_exclude and value_exclude.for_element(k),
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                )
                if not (exclude_none and value is None):
                    yield k, value

    def _calculate_keys(
        self,
        include: Optional[Union['AbstractSetIntStr', 'DictIntStrAny']],
        exclude: Optional[Union['AbstractSetIntStr', 'DictIntStrAny']],
        exclude_unset: bool,
        update: Optional['DictStrAny'] = None,
    ) -> Optional['SetStr']:
        if include is None and exclude is None and exclude_unset is False:
            return None

        if exclude_unset:
            keys = self.__fields_set__.copy()
        else:
            keys = set(self.__dict__.keys())

        if include is not None:
            if isinstance(include, dict):
                keys &= include.keys()
            else:
                keys &= include

        if update:
            keys -= update.keys()

        if exclude:
            if isinstance(exclude, dict):
                keys -= {k for k, v in exclude.items() if v is ...}
            else:
                keys -= exclude

        return keys

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseModel):
            return self.dict() == other.dict()
        else:
            return self.dict() == other

    def __repr_args__(self) -> 'ReprArgs':
        return self.__dict__.items()  # type: ignore

    @property
    def fields(self) -> Dict[str, ModelField]:
        warnings.warn('`fields` attribute is deprecated, use `__fields__` instead', DeprecationWarning)
        return self.__fields__

    def to_string(self, pretty: bool = False) -> str:
        warnings.warn('`model.to_string()` method is deprecated, use `str(model)` instead', DeprecationWarning)
        return str(self)

    @property
    def __values__(self) -> 'DictStrAny':
        warnings.warn('`__values__` attribute is deprecated, use `__dict__` instead', DeprecationWarning)
        return self.__dict__


def create_model(
    model_name: str,
    *,
    __config__: Type[BaseConfig] = None,
    __base__: Type[BaseModel] = None,
    __module__: Optional[str] = None,
    __validators__: Dict[str, classmethod] = None,
    **field_definitions: Any,
) -> Type[BaseModel]:
    """
    Dynamically create a model.
    :param model_name: name of the created model
    :param __config__: config class to use for the new model
    :param __base__: base class for the new model to inherit from
    :param __validators__: a dict of method names and @validator class methods
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
        if not is_valid_field(f_name):
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
    if __validators__:
        namespace.update(__validators__)
    namespace.update(fields)
    if __config__:
        namespace['Config'] = inherit_config(__config__, BaseConfig)

    return type(model_name, (__base__,), namespace)


_missing = object()


def validate_model(  # noqa: C901 (ignore complexity)
    model: Type[BaseModel], input_data: 'DictStrAny', cls: 'ModelOrDc' = None
) -> Tuple['DictStrAny', 'SetStr', Optional[ValidationError]]:
    """
    validate data against a model.
    """
    values = {}
    errors = []
    # input_data names, possibly alias
    names_used = set()
    # field names, never aliases
    fields_set = set()
    config = model.__config__
    check_extra = config.extra is not Extra.ignore
    cls_ = cls or model

    for validator in model.__pre_root_validators__:
        try:
            input_data = validator(cls_, input_data)
        except (ValueError, TypeError, AssertionError) as exc:
            return {}, set(), ValidationError([ErrorWrapper(exc, loc=ROOT_KEY)], cls_)

    for name, field in model.__fields__.items():
        if type(field.type_) == ForwardRef:
            raise ConfigError(
                f'field "{field.name}" not yet prepared so type is still a ForwardRef, '
                f'you might need to call {cls_.__name__}.update_forward_refs().'
            )

        value = input_data.get(field.alias, _missing)
        using_name = False
        if value is _missing and config.allow_population_by_field_name and field.alt_alias:
            value = input_data.get(field.name, _missing)
            using_name = True

        if value is _missing:
            if field.required:
                errors.append(ErrorWrapper(MissingError(), loc=field.alias))
                continue

            if field.default is None:
                # deepcopy is quite slow on None
                value = None
            else:
                value = deepcopy(field.default)

            if not config.validate_all and not field.validate_always:
                values[name] = value
                continue
        else:
            fields_set.add(name)
            if check_extra:
                names_used.add(field.name if using_name else field.alias)

        v_, errors_ = field.validate(value, values, loc=field.alias, cls=cls_)
        if isinstance(errors_, ErrorWrapper):
            errors.append(errors_)
        elif isinstance(errors_, list):
            errors.extend(errors_)
        else:
            values[name] = v_

    if check_extra:
        if isinstance(input_data, GetterDict):
            extra = input_data.extra_keys() - names_used
        else:
            extra = input_data.keys() - names_used
        if extra:
            fields_set |= extra
            if config.extra is Extra.allow:
                for f in extra:
                    values[f] = input_data[f]
            else:
                for f in sorted(extra):
                    errors.append(ErrorWrapper(ExtraError(), loc=f))

    for validator in model.__post_root_validators__:
        try:
            values = validator(cls_, values)
        except (ValueError, TypeError, AssertionError) as exc:
            errors.append(ErrorWrapper(exc, loc=ROOT_KEY))
            break

    if errors:
        return values, fields_set, ValidationError(errors, cls_)
    else:
        return values, fields_set, None
