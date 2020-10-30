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
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    no_type_check,
    overload,
)

from .class_validators import ValidatorGroup, extract_root_validators, extract_validators, inherit_validators
from .error_wrappers import ErrorWrapper, ValidationError
from .errors import ConfigError, DictError, ExtraError, MissingError
from .fields import SHAPE_MAPPING, ModelField, ModelPrivateAttr, PrivateAttr, Undefined
from .json import custom_pydantic_encoder, pydantic_encoder
from .parse import Protocol, load_file, load_str_bytes
from .schema import default_ref_template, model_schema
from .types import PyObject, StrBytes
from .typing import AnyCallable, ForwardRef, get_origin, is_classvar, resolve_annotations, update_field_forward_refs
from .utils import (
    ROOT_KEY,
    ClassAttribute,
    GetterDict,
    Representation,
    ValueItems,
    generate_model_signature,
    is_valid_field,
    is_valid_private_name,
    lenient_issubclass,
    sequence_like,
    smart_deepcopy,
    unique_list,
    validate_field_name,
)

if TYPE_CHECKING:
    from inspect import Signature

    import typing_extensions

    from .class_validators import ValidatorListDict
    from .types import ModelOrDc
    from .typing import (  # noqa: F401
        AbstractSetIntStr,
        CallableGenerator,
        DictAny,
        DictStrAny,
        MappingIntStrAny,
        ReprArgs,
        SetStr,
        TupleGenerator,
    )

    ConfigType = Type['BaseConfig']
    Model = TypeVar('Model', bound='BaseModel')

    class SchemaExtraCallable(typing_extensions.Protocol):
        @overload
        def __call__(self, schema: Dict[str, Any]) -> None:
            pass

        @overload  # noqa: F811
        def __call__(self, schema: Dict[str, Any], model_class: Type['Model']) -> None:  # noqa: F811
            pass


else:
    SchemaExtraCallable = Callable[..., None]

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
    schema_extra: Union[Dict[str, Any], 'SchemaExtraCallable'] = {}
    json_loads: Callable[[str], Any] = json.loads
    json_dumps: Callable[..., str] = json.dumps
    json_encoders: Dict[Type[Any], AnyCallable] = {}
    underscore_attrs_are_private: bool = False

    @classmethod
    def get_field_info(cls, name: str) -> Dict[str, Any]:
        fields_value = cls.fields.get(name)

        if isinstance(fields_value, str):
            field_info: Dict[str, Any] = {'alias': fields_value}
        elif isinstance(fields_value, dict):
            field_info = fields_value
        else:
            field_info = {}

        if 'alias' in field_info:
            field_info.setdefault('alias_priority', 2)

        if field_info.get('alias_priority', 0) <= 1 and cls.alias_generator:
            alias = cls.alias_generator(name)
            if not isinstance(alias, str):
                raise TypeError(f'Config.alias_generator must return str, not {alias.__class__}')
            field_info.update(alias=alias, alias_priority=1)
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


def validate_custom_root_type(fields: Dict[str, ModelField]) -> None:
    if len(fields) > 1:
        raise ValueError('__root__ cannot be mixed with other fields')


UNTOUCHED_TYPES = FunctionType, property, type, classmethod, staticmethod

# Note `ModelMetaclass` refers to `BaseModel`, but is also used to *create* `BaseModel`, so we need to add this extra
# (somewhat hacky) boolean to keep track of whether we've created the `BaseModel` class yet, and therefore whether it's
# safe to refer to it. If it *hasn't* been created, we assume that the `__new__` call we're in the middle of is for
# the `BaseModel` class, since that's defined immediately after the metaclass.
_is_base_model_class_defined = False


class ModelMetaclass(ABCMeta):
    @no_type_check  # noqa C901
    def __new__(mcs, name, bases, namespace, **kwargs):  # noqa C901
        fields: Dict[str, ModelField] = {}
        config = BaseConfig
        validators: 'ValidatorListDict' = {}

        pre_root_validators, post_root_validators = [], []
        private_attributes: Dict[str, ModelPrivateAttr] = {}
        slots: Set[str] = namespace.get('__slots__', ())
        slots = {slots} if isinstance(slots, str) else set(slots)

        for base in reversed(bases):
            if _is_base_model_class_defined and issubclass(base, BaseModel) and base != BaseModel:
                fields.update(smart_deepcopy(base.__fields__))
                config = inherit_config(base.__config__, config)
                validators = inherit_validators(base.__validators__, validators)
                pre_root_validators += base.__pre_root_validators__
                post_root_validators += base.__post_root_validators__
                private_attributes.update(base.__private_attributes__)

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
                        and not lenient_issubclass(get_origin(ann_type), Type)
                    ):
                        continue
                    fields[ann_name] = inferred = ModelField.infer(
                        name=ann_name,
                        value=value,
                        annotation=ann_type,
                        class_validators=vg.get_validators(ann_name),
                        config=config,
                    )
                elif ann_name not in namespace and config.underscore_attrs_are_private:
                    private_attributes[ann_name] = PrivateAttr()

            for var_name, value in namespace.items():
                can_be_changed = var_name not in class_vars and not isinstance(value, untouched_types)
                if isinstance(value, ModelPrivateAttr):
                    if not is_valid_private_name(var_name):
                        raise NameError(
                            f'Private attributes "{var_name}" must not be a valid field name; '
                            f'Use sunder or dunder names, e. g. "_{var_name}" or "__{var_name}__"'
                        )
                    private_attributes[var_name] = value
                elif config.underscore_attrs_are_private and is_valid_private_name(var_name) and can_be_changed:
                    private_attributes[var_name] = PrivateAttr(default=value)
                elif is_valid_field(var_name) and var_name not in annotations and can_be_changed:
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

        exclude_from_namespace = fields | private_attributes.keys() | {'__slots__'}
        new_namespace = {
            '__config__': config,
            '__fields__': fields,
            '__validators__': vg.validators,
            '__pre_root_validators__': unique_list(pre_root_validators + pre_rv_new),
            '__post_root_validators__': unique_list(post_root_validators + post_rv_new),
            '__schema_cache__': {},
            '__json_encoder__': staticmethod(json_encoder),
            '__custom_root_type__': _custom_root_type,
            '__private_attributes__': private_attributes,
            '__slots__': slots | private_attributes.keys(),
            **{n: v for n, v in namespace.items() if n not in exclude_from_namespace},
        }

        cls = super().__new__(mcs, name, bases, new_namespace, **kwargs)
        # set __signature__ attr only for model class, but not for its instances
        cls.__signature__ = ClassAttribute('__signature__', generate_model_signature(cls.__init__, fields, config))
        return cls


object_setattr = object.__setattr__


class BaseModel(Representation, metaclass=ModelMetaclass):
    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __fields__: Dict[str, ModelField] = {}
        __validators__: Dict[str, AnyCallable] = {}
        __pre_root_validators__: List[AnyCallable]
        __post_root_validators__: List[Tuple[bool, AnyCallable]]
        __config__: Type[BaseConfig] = BaseConfig
        __root__: Any = None
        __json_encoder__: Callable[[Any], Any] = lambda x: x
        __schema_cache__: 'DictAny' = {}
        __custom_root_type__: bool = False
        __signature__: 'Signature'
        __private_attributes__: Dict[str, Any]
        __fields_set__: SetStr = set()

    Config = BaseConfig
    __slots__ = ('__dict__', '__fields_set__')
    __doc__ = ''  # Null out the Representation docstring

    def __init__(__pydantic_self__, **data: Any) -> None:
        """
        Create a new model by parsing and validating input data from keyword arguments.

        Raises ValidationError if the input data cannot be parsed to form a valid model.
        """
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        values, fields_set, validation_error = validate_model(__pydantic_self__.__class__, data)
        if validation_error:
            raise validation_error
        object_setattr(__pydantic_self__, '__dict__', values)
        object_setattr(__pydantic_self__, '__fields_set__', fields_set)
        __pydantic_self__._init_private_attributes()

    @no_type_check
    def __setattr__(self, name, value):  # noqa: C901 (ignore complexity)
        if name in self.__private_attributes__:
            return object_setattr(self, name, value)

        if self.__config__.extra is not Extra.allow and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        elif not self.__config__.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and does not support item assignment')
        elif self.__config__.validate_assignment:
            new_values = {**self.__dict__, name: value}

            for validator in self.__pre_root_validators__:
                try:
                    new_values = validator(self.__class__, new_values)
                except (ValueError, TypeError, AssertionError) as exc:
                    raise ValidationError([ErrorWrapper(exc, loc=ROOT_KEY)], self.__class__)

            known_field = self.__fields__.get(name, None)
            if known_field:
                # We want to
                # - make sure validators are called without the current value for this field inside `values`
                # - keep other values (e.g. submodels) untouched (using `BaseModel.dict()` will change them into dicts)
                # - keep the order of the fields
                dict_without_original_value = {k: v for k, v in self.__dict__.items() if k != name}
                value, error_ = known_field.validate(value, dict_without_original_value, loc=name, cls=self.__class__)
                if error_:
                    raise ValidationError([error_], self.__class__)
                else:
                    new_values[name] = value

            errors = []
            for skip_on_failure, validator in self.__post_root_validators__:
                if skip_on_failure and errors:
                    continue
                try:
                    new_values = validator(self.__class__, new_values)
                except (ValueError, TypeError, AssertionError) as exc:
                    errors.append(ErrorWrapper(exc, loc=ROOT_KEY))
            if errors:
                raise ValidationError(errors, self.__class__)

        self.__dict__[name] = value
        self.__fields_set__.add(name)

    def __getstate__(self) -> 'DictAny':
        return {
            '__dict__': self.__dict__,
            '__fields_set__': self.__fields_set__,
            '__private_attribute_values__': {k: getattr(self, k, Undefined) for k in self.__private_attributes__},
        }

    def __setstate__(self, state: 'DictAny') -> None:
        object_setattr(self, '__dict__', state['__dict__'])
        object_setattr(self, '__fields_set__', state['__fields_set__'])
        for name, value in state.get('__private_attribute_values__', {}).items():
            if value is not Undefined:
                object_setattr(self, name, value)

    def _init_private_attributes(self) -> None:
        for name, private_attr in self.__private_attributes__.items():
            default = private_attr.get_default()
            if default is not Undefined:
                object_setattr(self, name, default)

    def dict(
        self,
        *,
        include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
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

        return dict(
            self._iter(
                to_dict=True,
                by_alias=by_alias,
                include=include,
                exclude=exclude,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        )

    def json(
        self,
        *,
        include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
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
                exc = TypeError(f'{cls.__name__} expected dict not {obj.__class__.__name__}')
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
        obj = load_file(
            path,
            proto=proto,
            content_type=content_type,
            encoding=encoding,
            allow_pickle=allow_pickle,
            json_loads=cls.__config__.json_loads,
        )
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
        object_setattr(m, '__dict__', values)
        object_setattr(m, '__fields_set__', fields_set)
        m._init_private_attributes()
        return m

    @classmethod
    def construct(cls: Type['Model'], _fields_set: Optional['SetStr'] = None, **values: Any) -> 'Model':
        """
        Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
        Default values are respected, but no other validation is performed.
        """
        m = cls.__new__(cls)
        # default field values
        fields_values = {name: field.get_default() for name, field in cls.__fields__.items() if not field.required}
        fields_values.update(values)
        object_setattr(m, '__dict__', fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        object_setattr(m, '__fields_set__', _fields_set)
        m._init_private_attributes()
        return m

    def copy(
        self: 'Model',
        *,
        include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
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

        v = dict(
            self._iter(to_dict=False, by_alias=False, include=include, exclude=exclude, exclude_unset=False),
            **(update or {}),
        )

        if deep:
            # chances of having empty dict here are quite low for using smart_deepcopy
            v = deepcopy(v)

        cls = self.__class__
        m = cls.__new__(cls)
        object_setattr(m, '__dict__', v)
        object_setattr(m, '__fields_set__', self.__fields_set__.copy())
        for name in self.__private_attributes__:
            value = getattr(self, name, Undefined)
            if value is not Undefined:
                if deep:
                    value = deepcopy(value)
                object_setattr(m, name, value)

        return m

    @classmethod
    def schema(cls, by_alias: bool = True, ref_template: str = default_ref_template) -> 'DictStrAny':
        cached = cls.__schema_cache__.get((by_alias, ref_template))
        if cached is not None:
            return cached
        s = model_schema(cls, by_alias=by_alias, ref_template=ref_template)
        cls.__schema_cache__[(by_alias, ref_template)] = s
        return s

    @classmethod
    def schema_json(
        cls, *, by_alias: bool = True, ref_template: str = default_ref_template, **dumps_kwargs: Any
    ) -> str:
        from .json import pydantic_encoder

        return cls.__config__.json_dumps(
            cls.schema(by_alias=by_alias, ref_template=ref_template), default=pydantic_encoder, **dumps_kwargs
        )

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
        elif cls.__custom_root_type__:
            return cls.parse_obj(value)
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
        include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']],
        exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']],
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
    ) -> Any:

        if isinstance(v, BaseModel):
            if to_dict:
                v_dict = v.dict(
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    include=include,
                    exclude=exclude,
                    exclude_none=exclude_none,
                )
                if '__root__' in v_dict:
                    return v_dict['__root__']
                return v_dict
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

        elif sequence_like(v):
            return v.__class__(
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

        elif isinstance(v, Enum) and getattr(cls.Config, 'use_enum_values', False):
            return v.value

        else:
            return v

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        """
        Try to update ForwardRefs on fields based on this Model, globalns and localns.
        """
        globalns = sys.modules[cls.__module__].__dict__.copy()
        globalns.setdefault(cls.__name__, cls)
        for f in cls.__fields__.values():
            update_field_forward_refs(f, globalns=globalns, localns=localns)

    def __iter__(self) -> 'TupleGenerator':
        """
        so `dict(model)` works
        """
        yield from self.__dict__.items()

    def _iter(
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
        exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> 'TupleGenerator':

        allowed_keys = self._calculate_keys(include=include, exclude=exclude, exclude_unset=exclude_unset)
        if allowed_keys is None and not (to_dict or by_alias or exclude_unset or exclude_defaults or exclude_none):
            # huge boost for plain _iter()
            yield from self.__dict__.items()
            return

        value_exclude = ValueItems(self, exclude) if exclude else None
        value_include = ValueItems(self, include) if include else None

        for field_key, v in self.__dict__.items():
            if (
                (allowed_keys is not None and field_key not in allowed_keys)
                or (exclude_none and v is None)
                or (exclude_defaults and getattr(self.__fields__.get(field_key), 'default', _missing) == v)
            ):
                continue
            if by_alias and field_key in self.__fields__:
                dict_key = self.__fields__[field_key].alias
            else:
                dict_key = field_key
            if to_dict or value_include or value_exclude:
                v = self._get_value(
                    v,
                    to_dict=to_dict,
                    by_alias=by_alias,
                    include=value_include and value_include.for_element(field_key),
                    exclude=value_exclude and value_exclude.for_element(field_key),
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                )
            yield dict_key, v

    def _calculate_keys(
        self,
        include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']],
        exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']],
        exclude_unset: bool,
        update: Optional['DictStrAny'] = None,
    ) -> Optional[AbstractSet[str]]:
        if include is None and exclude is None and exclude_unset is False:
            return None

        keys: AbstractSet[str]
        if exclude_unset:
            keys = self.__fields_set__.copy()
        else:
            keys = self.__dict__.keys()

        if include is not None:
            if isinstance(include, Mapping):
                keys &= include.keys()
            else:
                keys &= include

        if update:
            keys -= update.keys()

        if exclude:
            if isinstance(exclude, Mapping):
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


_is_base_model_class_defined = True


def create_model(
    __model_name: str,
    *,
    __config__: Type[BaseConfig] = None,
    __base__: Type[BaseModel] = None,
    __module__: str = __name__,
    __validators__: Dict[str, classmethod] = None,
    **field_definitions: Any,
) -> Type[BaseModel]:
    """
    Dynamically create a model.
    :param __model_name: name of the created model
    :param __config__: config class to use for the new model
    :param __base__: base class for the new model to inherit from
    :param __module__: module of the created model
    :param __validators__: a dict of method names and @validator class methods
    :param field_definitions: fields of the model (or extra fields if a base is supplied)
        in the format `<name>=(<type>, <default default>)` or `<name>=<default value>, e.g.
        `foobar=(str, ...)` or `foobar=123`, or, for complex use-cases, in the format
        `<name>=<FieldInfo>`, e.g. `foo=Field(default_factory=datetime.utcnow, alias='bar')`
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
                    'field definitions should either be a tuple of (<type>, <default>) or just a '
                    'default value, unfortunately this means tuples as '
                    'default values are not allowed'
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

    return type(__model_name, (__base__,), namespace)


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
        if field.type_.__class__ == ForwardRef:
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

            value = field.get_default()

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

    for skip_on_failure, validator in model.__post_root_validators__:
        if skip_on_failure and errors:
            continue
        try:
            values = validator(cls_, values)
        except (ValueError, TypeError, AssertionError) as exc:
            errors.append(ErrorWrapper(exc, loc=ROOT_KEY))

    if errors:
        return values, fields_set, ValidationError(errors, cls_)
    else:
        return values, fields_set, None
