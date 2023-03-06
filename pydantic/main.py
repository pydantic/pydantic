"""
Logic for creating models, could perhaps be renamed to `models.py`.
"""
from __future__ import annotations as _annotations

import typing
import warnings
from abc import ABCMeta
from collections import defaultdict
from contextvars import ContextVar
from copy import deepcopy
from enum import Enum
from functools import partial
from inspect import getdoc
from types import prepare_class, resolve_bases
from typing import Any, Generic

import typing_extensions
from pydantic_core import core_schema

from ._internal import _decorators, _generics, _model_construction, _repr, _typing_extra, _utils
from ._internal._fields import Undefined
from ._internal._generate_schema import get_type_ref
from ._internal._generics import (
    GENERIC_TYPES_CACHE,
    GenericTypesCacheKey,
    TypeVarType,
    check_parameters_count,
    iter_contained_typevars,
    replace_types,
)
from ._internal._self_type import BaseSelfType, get_self_type
from ._internal._utils import all_identical
from .config import BaseConfig, ConfigDict, Extra, build_config, get_config
from .errors import PydanticUserError
from .fields import Field, FieldInfo, ModelPrivateAttr
from .json import custom_pydantic_encoder, pydantic_encoder
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema, JsonSchemaMetadata

if typing.TYPE_CHECKING:
    from inspect import Signature

    from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator

    from ._internal._utils import AbstractSetIntStr, MappingIntStrAny

    AnyClassMethod = classmethod[Any]
    TupleGenerator = typing.Generator[tuple[str, Any], None, None]
    Model = typing.TypeVar('Model', bound='BaseModel')
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx = set[int] | set[str] | dict[int, Any] | dict[str, Any] | None

__all__ = 'BaseModel', 'create_model'

_object_setattr = _model_construction.object_setattr
# Note `ModelMetaclass` refers to `BaseModel`, but is also used to *create* `BaseModel`, so we need to add this extra
# (somewhat hacky) boolean to keep track of whether we've created the `BaseModel` class yet, and therefore whether it's
# safe to refer to it. If it *hasn't* been created, we assume that the `__new__` call we're in the middle of is for
# the `BaseModel` class, since that's defined immediately after the metaclass.
_base_class_defined = False


@typing_extensions.dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class ModelMetaclass(ABCMeta):
    def __new__(
        mcs,
        cls_name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        __pydantic_generic_origin__: type[BaseModel] | None = None,
        __pydantic_generic_args__: tuple[Any, ...] | None = None,
        **kwargs: Any,
    ) -> type:
        if _base_class_defined:
            config_new = build_config(cls_name, bases, namespace, kwargs)
            namespace['model_config'] = config_new
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

            validator_functions = _decorators.ValidationFunctions(bases)
            namespace[validator_functions.model_attribute] = validator_functions

            serializer_functions = _decorators.SerializationFunctions(bases)
            namespace[serializer_functions.model_attribute] = serializer_functions

            for name, value in namespace.items():
                found_validator = validator_functions.extract_decorator(name, value)
                if not found_validator:
                    serializer_functions.extract_decorator(name, value)

            if config_new['json_encoders']:
                json_encoder = partial(custom_pydantic_encoder, config_new['json_encoders'])
            else:
                json_encoder = pydantic_encoder  # type: ignore[assignment]
            namespace['__json_encoder__'] = staticmethod(json_encoder)
            namespace['__schema_cache__'] = {}

            if '__hash__' not in namespace and config_new['frozen']:

                def hash_func(self_: Any) -> int:
                    return hash(self_.__class__) + hash(tuple(self_.__dict__.values()))

                namespace['__hash__'] = hash_func

            cls: type[BaseModel] = super().__new__(mcs, cls_name, bases, namespace, **kwargs)  # type: ignore

            # TODO: cls.__concrete__ has been removed -- do we need to retain this for v1 compatibility?
            # TODO: cls.__parameters__ may be removed -- do we need to retain this for v1 compatibility?
            cls.__pydantic_generic_origin__ = __pydantic_generic_origin__
            cls.__pydantic_generic_args__ = __pydantic_generic_args__
            cls.__pydantic_generic_typevars_map__ = (
                None
                if __pydantic_generic_origin__ is None
                else dict(zip(iter_contained_typevars(__pydantic_generic_origin__), __pydantic_generic_args__ or ()))
            )
            _model_construction.complete_model_class(
                cls,
                cls_name,
                validator_functions,
                serializer_functions,
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
        return hasattr(instance, '__pydantic_validator__') and super().__instancecheck__(instance)


# TODO: Need to add some comments documenting how/why this ContextVar is used
#   Ideally move to the _generics module and wrap in a context manager that conveys intent
generic_recursion: ContextVar[dict[Any, int] | None] = ContextVar('generic_recursion', default=None)


class BaseModel(_repr.Representation, metaclass=ModelMetaclass):
    if typing.TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __pydantic_validator__: typing.ClassVar[SchemaValidator]
        __pydantic_core_schema__: typing.ClassVar[CoreSchema]
        __pydantic_serializer__: typing.ClassVar[SchemaSerializer]
        __pydantic_validator_functions__: typing.ClassVar[_decorators.ValidationFunctions]
        __pydantic_serializer_functions__: typing.ClassVar[_decorators.SerializationFunctions]
        model_fields: typing.ClassVar[dict[str, FieldInfo]] = {}
        __json_encoder__: typing.ClassVar[typing.Callable[[Any], Any]] = lambda x: x  # noqa: E731
        __schema_cache__: typing.ClassVar[dict[Any, Any]] = {}
        __signature__: typing.ClassVar[Signature]
        __private_attributes__: typing.ClassVar[dict[str, ModelPrivateAttr]]
        __class_vars__: typing.ClassVar[set[str]]
        __fields_set__: set[str] = set()
        __pydantic_generic_args__: typing.ClassVar[tuple[Any, ...] | None] = None
        __pydantic_generic_origin__: typing.ClassVar[type[BaseModel] | None] = None
        __pydantic_generic_typevars_map__: typing.ClassVar[dict[TypeVarType, Any] | None] = None
        # TODO: rename __parameters__ with __pydantic prefix
        # __parameters__: typing.ClassVar[tuple[TypeVarType, ...] | None] = None
    else:
        __pydantic_validator__ = _model_construction.MockValidator(
            'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly'
        )

    model_config = ConfigDict()
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
    def model_validate_json(cls: type[Model], json_data: str | bytes | bytearray) -> Model:
        values, fields_set = cls.__pydantic_validator__.validate_json(json_data)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', values)
        _object_setattr(m, '__fields_set__', fields_set)
        if hasattr(cls, '__pydantic_post_init__'):
            cls.__pydantic_post_init__(context=None)  # type: ignore[attr-defined]
        return m

    if typing.TYPE_CHECKING:
        # model_after_init is called after at the end of `__init__` if it's defined
        def model_post_init(self, **kwargs: Any) -> None:
            pass

    @typing.no_type_check
    def __setattr__(self, name, value):
        if name.startswith('_'):
            _object_setattr(self, name, value)
        elif self.model_config['frozen']:
            raise TypeError(f'"{self.__class__.__name__}" is frozen and does not support item assignment')
        elif self.model_config['validate_assignment']:
            values, fields_set = self.__pydantic_validator__.validate_assignment(name, value, self.__dict__)
            _object_setattr(self, '__dict__', values)
            self.__fields_set__ |= fields_set
        elif self.model_config['extra'] is not Extra.allow and name not in self.model_fields:
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
        mode: typing_extensions.Literal['json', 'python'] | str = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
        """
        return self.__pydantic_serializer__.to_python(
            self,
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> bytes:
        """
        Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.
        """
        return self.__pydantic_serializer__.to_json(
            self,
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

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

        # removing excluded fields from `__fields_set__`
        if exclude:
            fields_set -= set(exclude)

        return self._copy_and_set_values(values, fields_set, deep=deep)

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> typing.Dict[str, Any]:
        """
        To override the logic used to generate the JSON schema, you can create a subclass of GenerateJsonSchema
        with your desired modifications, then override this method on a custom base class and set the default
        value of `schema_generator` to be your subclass.
        """
        cached = cls.__schema_cache__.get((by_alias, ref_template))
        if cached is not None:
            return cached
        s = schema_generator(by_alias=by_alias, ref_template=ref_template).generate(cls.__pydantic_core_schema__)
        cls.__schema_cache__[(by_alias, ref_template)] = s
        return s

    @classmethod
    def model_json_schema_metadata(cls) -> JsonSchemaMetadata | None:
        """
        Overriding this method provides a simple way to modify certain aspects of the JSON schema generation.

        This is a convenience method primarily intended to control how the "generic" properties
        of the JSON schema are populated, or apply minor transformations through `extra_updates` or
        `modify_js_function`. See https://json-schema.org/understanding-json-schema/reference/generic.html
        and the comments surrounding the definition of `JsonSchemaMetadata` for more details.

        If you want to make more sweeping changes to how the JSON schema is generated, you will probably
        want to subclass `GenerateJsonSchema` and pass your subclass in the `schema_generator` argument to the
        `model_json_schema` method.
        """
        title = cls.model_config['title'] or cls.__name__
        description = getdoc(cls) or None
        return {'title': title, 'description': description}

    @classmethod
    def schema_json(
        cls, *, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE, **dumps_kwargs: Any
    ) -> str:
        from .json import pydantic_encoder

        return cls.model_config['json_dumps'](
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

        elif isinstance(v, Enum) and getattr(cls.model_config, 'use_enum_values', False):
            return v.value

        else:
            return v

    @classmethod
    def model_rebuild(
        cls,
        *,
        force: bool = False,
        raise_errors: bool = True,
        types_namespace: typing.Dict[str, Any] | None = None,
        typevars_map: typing.Dict[str, Any] | None = None,
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

            completed = _model_construction.complete_model_class(
                cls,
                cls.__name__,
                cls.__pydantic_validator_functions__,
                cls.__pydantic_serializer_functions__,
                cls.__bases__,
                raise_errors=raise_errors,
                types_namespace=types_namespace,
                typevars_map=typevars_map,
            )

            return completed

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

    def __class_getitem__(
        cls, typevar_values: type[Any] | tuple[type[Any], ...]
    ) -> type[BaseModel] | type[BaseSelfType]:
        def _cache_key(_params: Any) -> GenericTypesCacheKey:
            # TODO: This doesn't seem right if _params is a tuple, which it definitely can be...
            #   Revisit this after looking into the changes added with the types cache
            args = typing_extensions.get_args(_params)
            # python returns a list for Callables, which is not hashable
            if len(args) == 2 and isinstance(args[0], list):
                args = (tuple(args[0]), args[1])
            return cls, _params, args

        cache_key = _cache_key(typevar_values)
        cached = GENERIC_TYPES_CACHE.get(cache_key)
        if cached is not None:
            return cached

        if cls is BaseModel:
            raise TypeError('Type parameters should be placed on typing.Generic, not BaseModel')
        if not hasattr(cls, '__parameters__'):
            raise TypeError(f'{cls} cannot be parametrized because it does not inherit from typing.Generic')
        if not cls.__parameters__ and Generic not in cls.__bases__:
            raise TypeError(f'{cls} is not a generic class')

        if not isinstance(typevar_values, tuple):
            typevar_values = (typevar_values,)
        check_parameters_count(cls, typevar_values)

        # Build map from generic typevars to passed params
        typevars_map: dict[TypeVarType, type[Any]] = dict(zip(getattr(cls, '__parameters__', ()), typevar_values))
        need_to_rebuild = False
        if all_identical(typevars_map.keys(), typevars_map.values()) and typevars_map:
            submodel = cls  # if arguments are equal to parameters it's the same object
        else:
            parent_args = cls.__pydantic_generic_args__
            if not parent_args:
                args = typevar_values
            else:
                args = tuple(replace_types(arg, typevars_map) for arg in parent_args)

            origin = cls.__pydantic_generic_origin__ or cls
            model_name = origin.model_concrete_name(args)

            parent_calls = generic_recursion.get()
            if parent_calls is None:
                parent_calls = defaultdict(int)
            if parent_calls[(origin, args)] >= 2:
                self_type = get_self_type(
                    core_schema.definition_reference_schema(get_type_ref(origin, args_override=args)), origin, []
                )
                return self_type
            parent_calls[(origin, args)] += 1

            token = generic_recursion.set(parent_calls)

            submodel = _generics.create_generic_submodel(model_name, origin, args)
            generic_recursion.reset(token)
            need_to_rebuild = True

            # Update params
            new_params = tuple(
                {param: None for param in iter_contained_typevars(typevars_map.values())}
            )  # use dict as ordered set
            submodel.__parameters__ = new_params

        # Update cache
        GENERIC_TYPES_CACHE[_cache_key(typevar_values)] = submodel
        if len(typevar_values) == 1:
            GENERIC_TYPES_CACHE[_cache_key(typevar_values[0])] = submodel

        # Rebuild model
        if need_to_rebuild:
            # Doing the rebuild _after_ populating the cache prevents infinite recursion
            # submodel.model_rebuild(force=True, typevars_map=typevars_map)
            submodel.model_rebuild(force=True, raise_errors=False, typevars_map=typevars_map)

        return submodel

    @classmethod
    def model_concrete_name(cls, params: tuple[type[Any], ...]) -> str:
        """Compute class name for child classes.

        :param params: Tuple of types of the class . Given a generic class
            `Model` with 2 type variables and a concrete model `Model[str, int]`,
            the value `(str, int)` would be passed to `params`.
        :return: String representing the new class where `params` are
            passed to `cls` as type variables.

        This method can be overridden to achieve a custom naming scheme for generic BaseModels.
        """
        if not _generics.is_generic_model(cls):
            raise TypeError('Concrete names should only be generated for generic models.')

        param_names = [_repr.display_as_type(param) for param in params]
        params_component = ', '.join(param_names)
        return f'{cls.__name__}[{params_component}]'


_base_class_defined = True


@typing.overload
def create_model(
    __model_name: str,
    *,
    __config__: ConfigDict | type[BaseConfig] | None = None,
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
    __config__: ConfigDict | type[BaseConfig] | None = None,
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
    __config__: ConfigDict | type[BaseConfig] | None = None,
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
    :param __config__: config dict/class to use for the new model
    :param __base__: base class for the new model to inherit from
    :param __module__: module of the created model
    :param __validators__: a dict of method names and @validator class methods
    :param __cls_kwargs__: a dict for class creation
    :param __slots__: Deprecated, `__slots__` should not be passed to `create_model`
    :param field_definitions: fields of the model (or extra fields if a base is supplied)
        in the format `<name>=(<type>, <default value>)` or `<name>=<default value>, e.g.
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
        namespace['model_config'] = get_config(__config__)
    resolved_bases = resolve_bases(__base__)
    meta, ns, kwds = prepare_class(__model_name, resolved_bases, kwds=__cls_kwargs__)
    if resolved_bases is not __base__:
        ns['__orig_bases__'] = __base__
    namespace.update(ns)
    return meta(__model_name, resolved_bases, namespace, **kwds)
