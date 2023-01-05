"""
Logic for creating models, could perhaps be renamed to `models.py`.
"""
from __future__ import annotations as _annotations

import typing
import warnings
from abc import ABCMeta
from copy import deepcopy
from enum import Enum
from functools import partial
from types import prepare_class, resolve_bases
from typing import Any

import typing_extensions

from ._internal import _model_construction, _repr, _typing_extra, _utils, _validation_functions
from ._internal._fields import Undefined
from .config import BaseConfig, Extra, build_config, inherit_config
from .errors import PydanticUserError
from .fields import Field, FieldInfo, ModelPrivateAttr
from .json import custom_pydantic_encoder, pydantic_encoder
from .schema import default_ref_template, model_schema

if typing.TYPE_CHECKING:
    from inspect import Signature

    from pydantic_core import CoreSchema, SchemaValidator

    from ._internal._utils import AbstractSetIntStr, MappingIntStrAny

    AnyClassMethod = classmethod[Any]
    TupleGenerator = typing.Generator[tuple[str, Any], None, None]
    Model = typing.TypeVar('Model', bound='BaseModel')

__all__ = 'BaseModel', 'create_model'

_object_setattr = _model_construction.object_setattr
# Note `ModelMetaclass` refers to `BaseModel`, but is also used to *create* `BaseModel`, so we need to add this extra
# (somewhat hacky) boolean to keep track of whether we've created the `BaseModel` class yet, and therefore whether it's
# safe to refer to it. If it *hasn't* been created, we assume that the `__new__` call we're in the middle of is for
# the `BaseModel` class, since that's defined immediately after the metaclass.
_base_class_defined = False


@typing_extensions.dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class ModelMetaclass(ABCMeta):
    def __new__(mcs, cls_name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], **kwargs: Any) -> type:
        if _base_class_defined:
            __config__, new_model_config = build_config(cls_name, bases, namespace, kwargs)
            if new_model_config is not None:
                namespace['Config'] = new_model_config
            namespace['__config__'] = __config__

            namespace['__private_attributes__'] = private_attributes = _model_construction.inspect_namespace(namespace)
            if private_attributes:
                slots: set[str] = set(namespace.get('__slots__', ()))
                namespace['__slots__'] = slots | private_attributes.keys()

                if 'model_post_init' in namespace:
                    # if there are private_attributes and a model_post_init function, we wrap them both
                    # in a single function
                    namespace['_init_private_attributes'] = _model_construction.init_private_attributes

                    def __pydantic_post_init__(self_: Any, **kwargs: Any) -> None:
                        self_._init_private_attributes()
                        self_.model_post_init(**kwargs)

                    namespace['__pydantic_post_init__'] = __pydantic_post_init__
                else:
                    namespace['__pydantic_post_init__'] = _model_construction.init_private_attributes
            elif 'model_post_init' in namespace:
                namespace['__pydantic_post_init__'] = namespace['model_post_init']

            validator_functions = _validation_functions.ValidationFunctions(bases)
            namespace['__pydantic_validator_functions__'] = validator_functions

            for name, value in namespace.items():
                validator_functions.extract_validator(name, value)

            if __config__.json_encoders:
                json_encoder = partial(custom_pydantic_encoder, __config__.json_encoders)
            else:
                json_encoder = pydantic_encoder  # type: ignore[assignment]
            namespace['__json_encoder__'] = staticmethod(json_encoder)

            if '__hash__' not in namespace and __config__.frozen:

                def hash_func(self_: Any) -> int:
                    return hash(self_.__class__) + hash(tuple(self_.__dict__.values()))

                namespace['__hash__'] = hash_func

            cls: type[BaseModel] = super().__new__(mcs, cls_name, bases, namespace, **kwargs)  # type: ignore

            _model_construction.complete_model_class(
                cls,
                cls_name,
                validator_functions,
                bases,
                types_namespace=_typing_extra.parent_frame_namespace(),
                raise_errors=False,
            )
            return cls
        else:
            # this is the BaseModel class itself being created, no logic required
            return super().__new__(mcs, cls_name, bases, namespace, **kwargs)

    def __instancecheck__(self, instance: Any) -> bool:
        """
        Avoid calling ABC _abc_subclasscheck unless we're pretty sure.

        See #3829 and python/cpython#92810
        """
        return hasattr(instance, 'model_fields') and super().__instancecheck__(instance)


class BaseModel(_repr.Representation, metaclass=ModelMetaclass):
    if typing.TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __pydantic_validator__: typing.ClassVar[SchemaValidator]
        __pydantic_validation_schema__: typing.ClassVar[CoreSchema]
        __pydantic_validator_functions__: typing.ClassVar[_validation_functions.ValidationFunctions]
        model_fields: typing.ClassVar[dict[str, FieldInfo]] = {}
        __config__: typing.ClassVar[type[BaseConfig]] = BaseConfig
        __json_encoder__: typing.ClassVar[typing.Callable[[Any], Any]] = lambda x: x  # noqa: E731
        __schema_cache__: typing.ClassVar[dict[Any, Any]] = {}
        __signature__: typing.ClassVar[Signature]
        __private_attributes__: typing.ClassVar[dict[str, ModelPrivateAttr]]
        __class_vars__: typing.ClassVar[set[str]]
        __fields_set__: set[str] = set()
    else:
        __pydantic_validator__ = _model_construction.MockValidator(
            'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly'
        )

    Config = BaseConfig
    __slots__ = '__dict__', '__fields_set__'
    __doc__ = ''  # Null out the Representation docstring
    __pydantic_model_complete__ = False

    def __init__(__pydantic_self__, **data: Any) -> None:
        """
        Create a new model by parsing and validating input data from keyword arguments.

        Raises ValidationError if the input data cannot be parsed to form a valid model.

        Uses something other than `self` for the first arg to allow "self" as a field name.

        `__tracebackhide__` tells pytest and some other tools to omit the function from tracebacks
        """
        __tracebackhide__ = True
        values, fields_set = __pydantic_self__.__pydantic_validator__.validate_python(data)
        _object_setattr(__pydantic_self__, '__dict__', values)
        _object_setattr(__pydantic_self__, '__fields_set__', fields_set)
        if hasattr(__pydantic_self__, '__pydantic_post_init__'):
            __pydantic_self__.__pydantic_post_init__(context=None)

    if typing.TYPE_CHECKING:
        # model_after_init is called after at the end of `__init__` if it's defined
        def model_post_init(self, **kwargs: Any) -> None:
            pass

    @typing.no_type_check
    def __setattr__(self, name, value):
        if name.startswith('_'):
            _object_setattr(self, name, value)
        elif self.__config__.frozen:
            raise TypeError(f'"{self.__class__.__name__}" is frozen and does not support item assignment')
        elif self.__config__.validate_assignment:
            values, fields_set = self.__pydantic_validator__.validate_assignment(name, value, self.__dict__)
            _object_setattr(self, '__dict__', values)
            self.__fields_set__ |= fields_set
        elif self.__config__.extra is not Extra.allow and name not in self.model_fields:
            # TODO - matching error
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        else:
            self.__dict__[name] = value
            self.__fields_set__.add(name)

    def __getstate__(self) -> dict[Any, Any]:
        private_attrs = ((k, getattr(self, k, Undefined)) for k in self.__private_attributes__)
        return {
            '__dict__': self.__dict__,
            '__fields_set__': self.__fields_set__,
            '__private_attribute_values__': {k: v for k, v in private_attrs if v is not Undefined},
        }

    def __setstate__(self, state: dict[Any, Any]) -> None:
        _object_setattr(self, '__dict__', state['__dict__'])
        _object_setattr(self, '__fields_set__', state['__fields_set__'])
        for name, value in state.get('__private_attribute_values__', {}).items():
            _object_setattr(self, name, value)

    def model_dump(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        """
        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

        """
        if skip_defaults is not None:
            warnings.warn(
                f'{self.__class__.__name__}.model_dump(): "skip_defaults" is deprecated'
                ' and replaced by "exclude_unset"',
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

    def model_dump_json(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        encoder: typing.Callable[[Any], Any] | None = None,
        models_as_dict: bool = True,
        **dumps_kwargs: Any,
    ) -> str:
        """
        Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

        `encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
        """
        if skip_defaults is not None:
            warnings.warn(
                f'{self.__class__.__name__}.model_dump_json(): "skip_defaults" is deprecated'
                ' and replaced by "exclude_unset"',
                DeprecationWarning,
            )
            exclude_unset = skip_defaults
        encoder = typing.cast(typing.Callable[[Any], Any], encoder or self.__json_encoder__)

        # We don't directly call `self.model_dump()`, which does exactly this with `to_dict=True`
        # because we want to be able to keep raw `BaseModel` instances and not as `dict`.
        # This allows users to write custom JSON encoders for given `BaseModel` classes.
        data = dict(
            self._iter(
                to_dict=models_as_dict,
                by_alias=by_alias,
                include=include,
                exclude=exclude,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        )
        return self.__config__.json_dumps(data, default=encoder, **dumps_kwargs)

    @classmethod
    def model_validate(cls: type[Model], obj: Any) -> Model:
        values, fields_set = cls.__pydantic_validator__.validate_python(obj)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', values)
        _object_setattr(m, '__fields_set__', fields_set)
        if hasattr(cls, '__pydantic_post_init__'):
            cls.__pydantic_post_init__(context=None)  # type: ignore[attr-defined]
        return m

    @classmethod
    def from_orm(cls: type[Model], obj: Any) -> Model:
        # TODO remove
        return cls.model_validate(obj)

    @classmethod
    def model_construct(cls: type[Model], _fields_set: set[str] | None = None, **values: Any) -> Model:
        """
        Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
        Default values are respected, but no other validation is performed.
        Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
        """
        m = cls.__new__(cls)
        fields_values: dict[str, Any] = {}
        for name, field in cls.model_fields.items():
            if field.alias and field.alias in values:
                fields_values[name] = values[field.alias]
            elif name in values:
                fields_values[name] = values[name]
            elif not field.is_required():
                fields_values[name] = field.get_default()
        fields_values.update(values)
        _object_setattr(m, '__dict__', fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        _object_setattr(m, '__fields_set__', _fields_set)
        if hasattr(m, '__pydantic_post_init__'):
            m.__pydantic_post_init__(context=None)
        return m

    def _copy_and_set_values(self: Model, values: typing.Dict[str, Any], fields_set: set[str], *, deep: bool) -> Model:
        if deep:
            # chances of having empty dict here are quite low for using smart_deepcopy
            values = deepcopy(values)

        cls = self.__class__
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', values)
        _object_setattr(m, '__fields_set__', fields_set)
        for name in self.__private_attributes__:
            value = getattr(self, name, Undefined)
            if value is not Undefined:
                if deep:
                    value = deepcopy(value)
                _object_setattr(m, name, value)

        return m

    def copy(
        self: Model,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        update: typing.Dict[str, Any] | None = None,
        deep: bool = False,
    ) -> Model:
        """
        Duplicate a model, optionally choose which fields to include, exclude and change.

        :param include: fields to include in new model
        :param exclude: fields to exclude from new model, as with values this takes precedence over include
        :param update: values to change/add in the new model. Note: the data is not validated before creating
            the new model: you should trust this data
        :param deep: set to `True` to make a deep copy of the model
        :return: new model instance
        """

        values = dict(
            self._iter(to_dict=False, by_alias=False, include=include, exclude=exclude, exclude_unset=False),
            **(update or {}),
        )

        # new `__fields_set__` can have unset optional fields with a set value in `update` kwarg
        if update:
            fields_set = self.__fields_set__ | update.keys()
        else:
            fields_set = set(self.__fields_set__)

        return self._copy_and_set_values(values, fields_set, deep=deep)

    @classmethod
    def model_json_schema(
        cls, by_alias: bool = True, ref_template: str = default_ref_template
    ) -> typing.Dict[str, Any]:
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
            cls.model_json_schema(by_alias=by_alias, ref_template=ref_template),
            default=pydantic_encoder,
            **dumps_kwargs,
        )

    @classmethod
    @typing.no_type_check
    def _get_value(
        cls,
        v: Any,
        to_dict: bool,
        by_alias: bool,
        include: AbstractSetIntStr | MappingIntStrAny | None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
    ) -> Any:

        if isinstance(v, BaseModel):
            if to_dict:
                return v.model_dump(
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    include=include,
                    exclude=exclude,
                    exclude_none=exclude_none,
                )
            else:
                return v.copy(include=include, exclude=exclude)

        value_exclude = _utils.ValueItems(v, exclude) if exclude else None
        value_include = _utils.ValueItems(v, include) if include else None

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

        elif _utils.sequence_like(v):
            seq_args = (
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

            return v.__class__(*seq_args) if _typing_extra.is_namedtuple(v.__class__) else v.__class__(seq_args)

        elif isinstance(v, Enum) and getattr(cls.Config, 'use_enum_values', False):
            return v.value

        else:
            return v

    @classmethod
    def model_rebuild(
        cls, *, force: bool = False, raise_errors: bool = True, types_namespace: typing.Dict[str, Any] | None = None
    ) -> bool | None:
        """
        Try to (Re)construct the model schema.
        """
        if not force and cls.__pydantic_model_complete__:
            return None
        else:
            parents_namespace = _typing_extra.parent_frame_namespace()
            if types_namespace and parents_namespace:
                types_namespace = {**parents_namespace, **types_namespace}
            elif parents_namespace:
                types_namespace = parents_namespace

            return _model_construction.complete_model_class(
                cls,
                cls.__name__,
                cls.__pydantic_validator_functions__,
                cls.__bases__,
                raise_errors=raise_errors,
                types_namespace=types_namespace,
            )

    def __iter__(self) -> 'TupleGenerator':
        """
        so `dict(model)` works
        """
        yield from self.__dict__.items()

    def _iter(
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> 'TupleGenerator':

        # Merge field set excludes with explicit exclude parameter with explicit overriding field set options.
        # The extra "is not None" guards are not logically necessary but optimizes performance for the simple case.
        # if exclude is not None or self.__exclude_fields__ is not None:
        #     exclude = _utils.ValueItems.merge(self.__exclude_fields__, exclude)
        #
        # if include is not None or self.__include_fields__ is not None:
        #     include = _utils.ValueItems.merge(self.__include_fields__, include, intersect=True)

        allowed_keys = self._calculate_keys(
            include=include, exclude=exclude, exclude_unset=exclude_unset  # type: ignore
        )
        if allowed_keys is None and not (to_dict or by_alias or exclude_unset or exclude_defaults or exclude_none):
            # huge boost for plain _iter()
            yield from self.__dict__.items()
            return

        value_exclude = _utils.ValueItems(self, exclude) if exclude is not None else None
        value_include = _utils.ValueItems(self, include) if include is not None else None

        for field_key, v in self.__dict__.items():
            if (allowed_keys is not None and field_key not in allowed_keys) or (exclude_none and v is None):
                continue

            if exclude_defaults:
                try:
                    field = self.model_fields[field_key]
                except KeyError:
                    pass
                else:
                    if not field.is_required() and field.default == v:
                        continue

            if by_alias and field_key in self.model_fields:
                dict_key = self.model_fields[field_key].alias or field_key
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
        include: MappingIntStrAny | None,
        exclude: MappingIntStrAny | None,
        exclude_unset: bool,
        update: typing.Dict[str, Any] | None = None,
    ) -> typing.AbstractSet[str] | None:
        if include is None and exclude is None and exclude_unset is False:
            return None

        keys: typing.AbstractSet[str]
        if exclude_unset:
            keys = self.__fields_set__.copy()
        else:
            keys = self.__dict__.keys()

        if include is not None:
            keys &= include.keys()

        if update:
            keys -= update.keys()

        if exclude:
            keys -= {k for k, v in exclude.items() if _utils.ValueItems.is_true(v)}

        return keys

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseModel):
            return self.model_dump() == other.model_dump()
        else:
            return self.model_dump() == other

    def __repr_args__(self) -> _repr.ReprArgs:
        return [
            (k, v)
            for k, v in self.__dict__.items()
            if not k.startswith('_') and (k not in self.model_fields or self.model_fields[k].repr)
        ]


_base_class_defined = True


@typing.overload
def create_model(
    __model_name: str,
    *,
    __config__: type[BaseConfig] | None = None,
    __base__: None = None,
    __module__: str = __name__,
    __validators__: dict[str, AnyClassMethod] = None,
    __cls_kwargs__: dict[str, Any] = None,
    **field_definitions: Any,
) -> type[Model]:
    ...


@typing.overload
def create_model(
    __model_name: str,
    *,
    __config__: type[BaseConfig] | None = None,
    __base__: type[Model] | tuple[type[Model], ...],
    __module__: str = __name__,
    __validators__: dict[str, AnyClassMethod] = None,
    __cls_kwargs__: dict[str, Any] = None,
    **field_definitions: Any,
) -> type[Model]:
    ...


def create_model(
    __model_name: str,
    *,
    __config__: type[BaseConfig] | None = None,
    __base__: type[Model] | tuple[type[Model], ...] | None = None,
    __module__: str = __name__,
    __validators__: dict[str, AnyClassMethod] = None,
    __cls_kwargs__: dict[str, Any] = None,
    __slots__: tuple[str, ...] | None = None,
    **field_definitions: Any,
) -> type[Model]:
    """
    Dynamically create a model.
    :param __model_name: name of the created model
    :param __config__: config class to use for the new model
    :param __base__: base class for the new model to inherit from
    :param __module__: module of the created model
    :param __validators__: a dict of method names and @validator class methods
    :param __cls_kwargs__: a dict for class creation
    :param __slots__: Deprecated, `__slots__` should not be passed to `create_model`
    :param field_definitions: fields of the model (or extra fields if a base is supplied)
        in the format `<name>=(<type>, <default default>)` or `<name>=<default value>, e.g.
        `foobar=(str, ...)` or `foobar=123`, or, for complex use-cases, in the format
        `<name>=<Field>` or `<name>=(<type>, <FieldInfo>)`, e.g.
        `foo=Field(datetime, default_factory=datetime.utcnow, alias='bar')` or
        `foo=(str, FieldInfo(title='Foo'))`
    """
    if __slots__ is not None:
        # __slots__ will be ignored from here on
        warnings.warn('__slots__ should not be passed to create_model', RuntimeWarning)

    if __base__ is not None:
        if __config__ is not None:
            raise PydanticUserError('to avoid confusion __config__ and __base__ cannot be used together')
        if not isinstance(__base__, tuple):
            __base__ = (__base__,)
    else:
        __base__ = (typing.cast(typing.Type['Model'], BaseModel),)

    __cls_kwargs__ = __cls_kwargs__ or {}

    fields = {}
    annotations = {}

    for f_name, f_def in field_definitions.items():
        if f_name.startswith('_'):
            warnings.warn(f'fields may not start with an underscore, ignoring "{f_name}"', RuntimeWarning)
        if isinstance(f_def, tuple):
            try:
                f_annotation, f_value = f_def
            except ValueError as e:
                raise PydanticUserError(
                    'field definitions should either be a tuple of (<type>, <default>) or just a '
                    'default value, unfortunately this means tuples as '
                    'default values are not allowed'
                ) from e
        else:
            f_annotation, f_value = None, f_def

        if f_annotation:
            annotations[f_name] = f_annotation
        fields[f_name] = f_value

    namespace: dict[str, Any] = {'__annotations__': annotations, '__module__': __module__}
    if __validators__:
        namespace.update(__validators__)
    namespace.update(fields)
    if __config__:
        namespace['Config'] = inherit_config(__config__, BaseConfig)
    resolved_bases = resolve_bases(__base__)
    meta, ns, kwds = prepare_class(__model_name, resolved_bases, kwds=__cls_kwargs__)
    if resolved_bases is not __base__:
        ns['__orig_bases__'] = __base__
    namespace.update(ns)
    return meta(__model_name, resolved_bases, namespace, **kwds)
