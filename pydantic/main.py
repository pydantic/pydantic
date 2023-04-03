"""
Logic for creating models, could perhaps be renamed to `models.py`.
"""
from __future__ import annotations as _annotations

import typing
import warnings
from abc import ABCMeta
from copy import copy, deepcopy
from inspect import getdoc
from pathlib import Path
from types import prepare_class, resolve_bases
from typing import Any, Generic

import pydantic_core
import typing_extensions

from ._internal import (
    _decorators,
    _forward_ref,
    _generics,
    _model_construction,
    _repr,
    _typing_extra,
    _utils,
)
from ._internal._fields import Undefined
from .config import BaseConfig, ConfigDict, Extra, build_config, get_config
from .deprecated import copy_internals as _deprecated_copy_internals
from .deprecated import parse as _deprecated_parse
from .errors import PydanticUndefinedAnnotation, PydanticUserError
from .fields import Field, FieldInfo, ModelPrivateAttr
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema, JsonSchemaValue, model_json_schema

if typing.TYPE_CHECKING:
    from inspect import Signature

    from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator

    from ._internal._generate_schema import GenerateSchema
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


@typing_extensions.dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
class ModelMetaclass(ABCMeta):
    def __new__(
        mcs,
        cls_name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        __pydantic_generic_origin__: type[BaseModel] | None = None,
        __pydantic_generic_args__: tuple[Any, ...] | None = None,
        __pydantic_generic_parameters__: tuple[Any, ...] | None = None,
        __pydantic_reset_parent_namespace__: bool = True,
        **kwargs: Any,
    ) -> type:
        if _base_class_defined:
            base_field_names, class_vars, base_private_attributes = _collect_bases_data(bases)

            config_new = build_config(cls_name, bases, namespace, kwargs)
            namespace['model_config'] = config_new
            private_attributes = _model_construction.inspect_namespace(
                namespace, config_new.get('ignored_types', ()), class_vars, base_field_names
            )
            if private_attributes:
                slots: set[str] = set(namespace.get('__slots__', ()))
                namespace['__slots__'] = slots | private_attributes.keys()

                if 'model_post_init' in namespace:
                    # if there are private_attributes and a model_post_init function, we wrap them both
                    # in a single function
                    namespace['_init_private_attributes'] = _model_construction.init_private_attributes

                    def __pydantic_post_init__(self_: Any, context: Any) -> None:
                        self_._init_private_attributes(context)
                        self_.model_post_init(context)

                    namespace['__pydantic_post_init__'] = __pydantic_post_init__
                else:
                    namespace['__pydantic_post_init__'] = _model_construction.init_private_attributes
            elif 'model_post_init' in namespace:
                namespace['__pydantic_post_init__'] = namespace['model_post_init']

            namespace['__class_vars__'] = class_vars
            namespace['__private_attributes__'] = {**base_private_attributes, **private_attributes}

            if '__hash__' not in namespace and config_new['frozen']:

                def hash_func(self_: Any) -> int:
                    return hash(self_.__class__) + hash(tuple(self_.__dict__.values()))

                namespace['__hash__'] = hash_func

            cls: type[BaseModel] = super().__new__(mcs, cls_name, bases, namespace, **kwargs)  # type: ignore

            cls.__pydantic_decorators__ = _decorators.gather_decorator_functions(cls)

            # FIXME all generics related attributes should be moved into a dict, like `__pydantic_decorators__`
            parent_typevars_map = {}
            for base in bases:
                base_typevars_map = getattr(base, '__pydantic_generic_typevars_map__', None)
                if base_typevars_map:
                    parent_typevars_map.update(base_typevars_map)

            cls.__pydantic_generic_args__ = __pydantic_generic_args__
            cls.__pydantic_generic_origin__ = __pydantic_generic_origin__
            cls.__pydantic_generic_parameters__ = __pydantic_generic_parameters__ or getattr(
                cls, '__parameters__', None
            )
            cls.__pydantic_generic_defaults__ = None if not cls.__pydantic_generic_parameters__ else {}
            if __pydantic_generic_origin__ is None:
                cls.__pydantic_generic_typevars_map__ = None
            else:
                new_typevars_map = dict(
                    zip(_generics.iter_contained_typevars(__pydantic_generic_origin__), __pydantic_generic_args__ or ())
                )
                cls.__pydantic_generic_typevars_map__ = {**parent_typevars_map, **new_typevars_map}

            cls.__pydantic_model_complete__ = False  # Ensure this specific class gets completed

            # preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487
            # for attributes not in `new_namespace` (e.g. private attributes)
            for name, obj in private_attributes.items():
                set_name = getattr(obj, '__set_name__', None)
                if callable(set_name):
                    set_name(cls, name)

            if __pydantic_reset_parent_namespace__:
                cls.__pydantic_parent_namespace__ = _typing_extra.parent_frame_namespace()
            parent_namespace = getattr(cls, '__pydantic_parent_namespace__', None)

            types_namespace = _model_construction.get_model_types_namespace(cls, parent_namespace)
            _model_construction.set_model_fields(cls, bases, types_namespace)
            _model_construction.complete_model_class(
                cls,
                cls_name,
                types_namespace,
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


class BaseModel(_repr.Representation, metaclass=ModelMetaclass):
    if typing.TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __pydantic_validator__: typing.ClassVar[SchemaValidator]
        __pydantic_core_schema__: typing.ClassVar[CoreSchema]
        __pydantic_serializer__: typing.ClassVar[SchemaSerializer]
        __pydantic_decorators__: typing.ClassVar[_decorators.DecoratorInfos]
        """metadata for `@validator`, `@root_validator` and `@serializer` decorators"""
        model_fields: typing.ClassVar[dict[str, FieldInfo]] = {}
        __signature__: typing.ClassVar[Signature]
        __private_attributes__: typing.ClassVar[dict[str, ModelPrivateAttr]]
        __class_vars__: typing.ClassVar[set[str]]
        __fields_set__: set[str] = set()
        __pydantic_generic_args__: typing.ClassVar[tuple[Any, ...] | None]
        __pydantic_generic_defaults__: typing.ClassVar[dict[str, Any] | None]
        __pydantic_generic_origin__: typing.ClassVar[type[BaseModel] | None]
        __pydantic_generic_parameters__: typing.ClassVar[tuple[_typing_extra.TypeVarType, ...] | None]
        __pydantic_generic_typevars_map__: typing.ClassVar[dict[_typing_extra.TypeVarType, Any] | None]
        __pydantic_parent_namespace__: typing.ClassVar[dict[str, Any] | None]
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
        """
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        __pydantic_self__.__pydantic_validator__.validate_python(data, self_instance=__pydantic_self__)

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[BaseModel], gen_schema: GenerateSchema) -> CoreSchema:
        return gen_schema.model_schema(cls)

    @classmethod
    def model_validate(
        cls: type[Model], obj: Any, *, strict: bool | None = None, context: dict[str, Any] | None = None
    ) -> Model:
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return cls.__pydantic_validator__.validate_python(obj, strict=strict, context=context)

    @classmethod
    def model_validate_json(
        cls: type[Model],
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
    ) -> Model:
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return cls.__pydantic_validator__.validate_json(json_data, strict=strict, context=context)

    if typing.TYPE_CHECKING:
        # model_after_init is called after at the end of `__init__` if it's defined
        def model_post_init(self, _context: Any) -> None:
            pass

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__class_vars__:
            raise AttributeError(
                f'"{name}" is a ClassVar of `{self.__class__.__name__}` and cannot be set on an instance. '
                f'If you want to set a value on the class, use `{self.__class__.__name__}.{name} = value`.'
            )
        if name.startswith('_'):
            _object_setattr(self, name, value)
        elif self.model_config['frozen']:
            raise TypeError(f'"{self.__class__.__name__}" is frozen and does not support item assignment')
        elif self.model_config['validate_assignment']:
            self.__pydantic_validator__.validate_assignment(self, name, value)
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
    ) -> str:
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
        ).decode()

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
                fields_values[name] = field.get_default(call_default_factory=True)
        fields_values.update(values)
        _object_setattr(m, '__dict__', fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        _object_setattr(m, '__fields_set__', _fields_set)
        if hasattr(m, '__pydantic_post_init__'):
            m.__pydantic_post_init__(context=None)
        return m

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> dict[str, Any]:
        """
        To override the logic used to generate the JSON schema, you can create a subclass of GenerateJsonSchema
        with your desired modifications, then override this method on a custom base class and set the default
        value of `schema_generator` to be your subclass.
        """
        return model_json_schema(cls, by_alias=by_alias, ref_template=ref_template, schema_generator=schema_generator)

    @classmethod
    def model_modify_json_schema(cls, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """
        Overriding this method provides a simple way to modify the JSON schema generated for the model.

        This is a convenience method primarily intended to control how the "generic" properties of the JSON schema
        are populated. See https://json-schema.org/understanding-json-schema/reference/generic.html for more details.

        If you want to make more sweeping changes to how the JSON schema is generated, you will probably want to create
        a subclass of `GenerateJsonSchema` and pass it as `schema_generator` in `BaseModel.model_json_schema`.
        """
        metadata = {'title': cls.model_config['title'] or cls.__name__, 'description': getdoc(cls) or None}
        metadata = {k: v for k, v in metadata.items() if v is not None}
        return {**metadata, **json_schema}

    @classmethod
    def model_rebuild(
        cls,
        *,
        force: bool = False,
        raise_errors: bool = True,
        _parent_namespace_depth: int = 2,
    ) -> bool | None:
        """
        Try to (Re)construct the model schema.
        """
        if not force and cls.__pydantic_model_complete__:
            return None
        else:
            if _parent_namespace_depth > 0:
                frame_parent_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth) or {}
                cls_parent_ns = cls.__pydantic_parent_namespace__ or {}
                cls.__pydantic_parent_namespace__ = {**cls_parent_ns, **frame_parent_ns}

            types_namespace = cls.__pydantic_parent_namespace__

            types_namespace = _model_construction.get_model_types_namespace(cls, types_namespace)
            return _model_construction.complete_model_class(
                cls,
                cls.__name__,
                types_namespace,
                raise_errors=raise_errors,
            )

    def __iter__(self) -> TupleGenerator:
        """
        so `dict(model)` works
        """
        yield from self.__dict__.items()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseModel):
            return False

        # When comparing instances of generic types for equality, as long as all field values are equal,
        # only require their generic origin types to be equal, rather than exact type equality.
        # This prevents headaches like MyGeneric(x=1) != MyGeneric[Any](x=1).
        self_type = getattr(self, '__pydantic_generic_origin__', None) or self.__class__
        other_type = getattr(other, '__pydantic_generic_origin__', None) or other.__class__

        if self_type != other_type:
            return False

        if self.__dict__ != other.__dict__:
            return False

        # If the types and field values match, check for equality of private attributes
        for k in self.__private_attributes__:
            if getattr(self, k, Undefined) != getattr(other, k, Undefined):
                return False

        return True

    def model_copy(self: Model, *, update: dict[str, Any] | None = None, deep: bool = False) -> Model:
        """
        Returns a copy of the model.

        :param update: values to change/add in the new model. Note: the data is not validated before creating
            the new model: you should trust this data
        :param deep: set to `True` to make a deep copy of the model
        :return: new model instance
        """
        copied = self.__deepcopy__() if deep else self.__copy__()
        if update:
            copied.__dict__.update(update)
            copied.__fields_set__.update(update.keys())
        return copied

    def __copy__(self: Model) -> Model:
        """
        Returns a shallow copy of the model
        """
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', copy(self.__dict__))
        _object_setattr(m, '__fields_set__', copy(self.__fields_set__))
        for name in self.__private_attributes__:
            value = getattr(self, name, Undefined)
            if value is not Undefined:
                _object_setattr(m, name, value)
        return m

    def __deepcopy__(self: Model, memo: dict[int, Any] | None = None) -> Model:
        """
        Returns a deep copy of the model
        """
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', deepcopy(self.__dict__, memo=memo))
        # This next line doesn't need a deepcopy because __fields_set__ is a set[str],
        # and attempting a deepcopy would be marginally slower.
        _object_setattr(m, '__fields_set__', copy(self.__fields_set__))
        for name in self.__private_attributes__:
            value = getattr(self, name, Undefined)
            if value is not Undefined:
                _object_setattr(m, name, deepcopy(value, memo=memo))
        return m

    def __repr_args__(self) -> _repr.ReprArgs:
        return [
            (k, v)
            for k, v in self.__dict__.items()
            if not k.startswith('_') and (k not in self.model_fields or self.model_fields[k].repr)
        ]

    def __class_getitem__(
        cls, typevar_values: type[Any] | tuple[type[Any], ...]
    ) -> type[BaseModel] | _forward_ref.PydanticForwardRef | _forward_ref.PydanticRecursiveRef:
        cached = _generics.get_cached_generic_type_early(cls, typevar_values)
        if cached is not None:
            return cached

        if cls is BaseModel:
            raise TypeError('Type parameters should be placed on typing.Generic, not BaseModel')
        if not hasattr(cls, '__parameters__'):
            raise TypeError(f'{cls} cannot be parametrized because it does not inherit from typing.Generic')
        if not cls.__pydantic_generic_parameters__ and Generic not in cls.__bases__:
            raise TypeError(f'{cls} is not a generic class')

        if not isinstance(typevar_values, tuple):
            typevar_values = (typevar_values,)
        _generics.check_parameters_count(cls, typevar_values)

        # Build map from generic typevars to passed params
        typevars_map: dict[_typing_extra.TypeVarType, type[Any]] = dict(
            zip(cls.__pydantic_generic_parameters__ or (), typevar_values)
        )

        if _utils.all_identical(typevars_map.keys(), typevars_map.values()) and typevars_map:
            submodel = cls  # if arguments are equal to parameters it's the same object
            _generics.set_cached_generic_type(cls, typevar_values, submodel)
        else:
            parent_args = cls.__pydantic_generic_args__
            if not parent_args:
                args = typevar_values
            else:
                args = tuple(_generics.replace_types(arg, typevars_map) for arg in parent_args)

            origin = cls.__pydantic_generic_origin__ or cls
            model_name = origin.model_parametrized_name(args)
            params = tuple(
                {param: None for param in _generics.iter_contained_typevars(typevars_map.values())}
            )  # use dict as ordered set

            with _generics.generic_recursion_self_type(origin, args) as maybe_self_type:
                if maybe_self_type is not None:
                    return maybe_self_type

                cached = _generics.get_cached_generic_type_late(cls, typevar_values, origin, args)
                if cached is not None:
                    return cached

                # Attempt to rebuild the origin in case new types have been defined
                try:
                    # depth 3 gets you above this __class_getitem__ call
                    origin.model_rebuild(_parent_namespace_depth=3)
                except PydanticUndefinedAnnotation:
                    # It's okay if it fails, it just means there are still undefined types
                    # that could be evaluated later.
                    # TODO: Presumably we should error if validation is attempted here?
                    pass

                submodel = _generics.create_generic_submodel(model_name, origin, args, params)

                # Update cache
                _generics.set_cached_generic_type(cls, typevar_values, submodel, origin, args)

                # Doing the rebuild _after_ populating the cache prevents infinite recursion
                submodel.model_rebuild(
                    force=True,
                    raise_errors=False,
                    _parent_namespace_depth=0,
                )

        return submodel

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        """
        Compute class name for parametrizations of generic classes.

        :param params: Tuple of types of the class . Given a generic class
            `Model` with 2 type variables and a concrete model `Model[str, int]`,
            the value `(str, int)` would be passed to `params`.
        :return: String representing the new class where `params` are
            passed to `cls` as type variables.

        This method can be overridden to achieve a custom naming scheme for generic BaseModels.
        """
        if not issubclass(cls, Generic):  # type: ignore[arg-type]
            raise TypeError('Concrete names should only be generated for generic models.')

        # Any strings received should represent forward references, so we handle them specially below.
        # If we eventually move toward wrapping them in a ForwardRef in __class_getitem__ in the future,
        # we may be able to remove this special case.
        param_names = [param if isinstance(param, str) else _repr.display_as_type(param) for param in params]
        params_component = ', '.join(param_names)
        return f'{cls.__name__}[{params_component}]'

    # ##### Deprecated methods from v1 #####
    def dict(
        self,
        *,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> typing.Dict[str, Any]:  # noqa UP006
        warnings.warn('The `dict` method is deprecated; use `model_dump` instead.', DeprecationWarning)
        return self.model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def json(
        self,
        *,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        # TODO: What do we do about the following arguments?
        #   Do they need to go on model_config now, and get used by the serializer?
        encoder: typing.Callable[[Any], Any] | None = Undefined,  # type: ignore[assignment]
        models_as_dict: bool = Undefined,  # type: ignore[assignment]
        **dumps_kwargs: Any,
    ) -> str:
        warnings.warn('The `json` method is deprecated; use `model_dump_json` instead.', DeprecationWarning)
        if encoder is not Undefined:
            raise TypeError('The `encoder` argument is no longer supported; use field serializers instead.')
        if models_as_dict is not Undefined:
            raise TypeError('The `models_as_dict` argument is no longer supported; use a model serializer instead.')
        if dumps_kwargs:
            raise TypeError('`dumps_kwargs` keyword arguments are no longer supported.')
        return self.model_dump_json(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @classmethod
    def parse_obj(cls: type[Model], obj: Any) -> Model:
        warnings.warn('The `parse_obj` method is deprecated; use `model_validate` instead.', DeprecationWarning)
        return cls.model_validate(obj)

    @classmethod
    def parse_raw(
        cls: type[Model],
        b: str | bytes,
        *,
        content_type: str = None,
        encoding: str = 'utf8',
        proto: _deprecated_parse.Protocol = None,
        allow_pickle: bool = False,
    ) -> Model:
        warnings.warn(
            'The `parse_raw` method is deprecated; if your data is JSON use `model_json_validate`, '
            'otherwise load the data then use `model_validate` instead.',
            DeprecationWarning,
        )
        try:
            obj = _deprecated_parse.load_str_bytes(
                b,
                proto=proto,
                content_type=content_type,
                encoding=encoding,
                allow_pickle=allow_pickle,
            )
        except (ValueError, TypeError) as exc:
            import json

            # try to match V1
            if isinstance(exc, UnicodeDecodeError):
                type_str = 'value_error.unicodedecode'
            elif isinstance(exc, json.JSONDecodeError):
                type_str = 'value_error.jsondecode'
            elif isinstance(exc, ValueError):
                type_str = 'value_error'
            else:
                type_str = 'type_error'

            # ctx is missing here, but since we've added `input` to the error, we're not pretending it's the same
            error: pydantic_core.InitErrorDetails = {
                'type': pydantic_core.PydanticCustomError(type_str, str(exc)),
                'loc': ('__root__',),
                'input': b,
            }
            raise pydantic_core.ValidationError(cls.__name__, [error])
        return cls.model_validate(obj)

    @classmethod
    def parse_file(
        cls: type[Model],
        path: str | Path,
        *,
        content_type: str = None,
        encoding: str = 'utf8',
        proto: _deprecated_parse.Protocol = None,
        allow_pickle: bool = False,
    ) -> Model:
        warnings.warn(
            'The `parse_file` method is deprecated; load the data from file, then if your data is JSON '
            'use `model_json_validate` otherwise `model_validate` instead.',
            DeprecationWarning,
        )
        obj = _deprecated_parse.load_file(
            path,
            proto=proto,
            content_type=content_type,
            encoding=encoding,
            allow_pickle=allow_pickle,
        )
        return cls.parse_obj(obj)

    @classmethod
    def from_orm(cls: type[Model], obj: Any) -> Model:
        warnings.warn(
            'The `from_orm` method is deprecated; set model_config["from_attributes"]=True '
            'and use `model_validate` instead.',
            DeprecationWarning,
        )
        if not cls.model_config['from_attributes']:
            raise PydanticUserError('You must set the config attribute `from_attributes=True` to use from_orm')
        return cls.model_validate(obj)

    @classmethod
    def construct(cls: type[Model], _fields_set: set[str] | None = None, **values: Any) -> Model:
        warnings.warn('The `construct` method is deprecated; use `model_construct` instead.', DeprecationWarning)
        return cls.model_construct(_fields_set=_fields_set, **values)

    def copy(
        self: Model,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        update: typing.Dict[str, Any] | None = None,  # noqa UP006
        deep: bool = False,
    ) -> Model:
        """
        This method is now deprecated; use `model_copy` instead. If you need include / exclude, use:

            data = self.model_dump(include=include, exclude=exclude, round_trip=True)
            data = {**data, **(update or {})}
            copied = self.model_validate(data)
        """
        warnings.warn(
            'The `copy` method is deprecated; use `model_copy` instead. '
            'See the docstring of `BaseModel.copy` for details about how to handle `include` and `exclude`.',
            DeprecationWarning,
        )

        values = dict(
            _deprecated_copy_internals._iter(
                self, to_dict=False, by_alias=False, include=include, exclude=exclude, exclude_unset=False
            ),
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

        return _deprecated_copy_internals._copy_and_set_values(self, values, fields_set, deep=deep)

    @classmethod
    def schema(
        cls, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE
    ) -> typing.Dict[str, Any]:  # noqa UP006
        warnings.warn('The `schema` method is deprecated; use `model_json_schema` instead.', DeprecationWarning)
        return cls.model_json_schema(by_alias=by_alias, ref_template=ref_template)

    @classmethod
    def schema_json(
        cls, *, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE, **dumps_kwargs: Any
    ) -> str:
        import json

        warnings.warn(
            'The `schema_json` method is deprecated; use `model_json_schema` and json.dumps instead.',
            DeprecationWarning,
        )
        from .deprecated.json import pydantic_encoder

        return json.dumps(
            cls.model_json_schema(by_alias=by_alias, ref_template=ref_template),
            default=pydantic_encoder,
            **dumps_kwargs,
        )

    @classmethod
    def validate(cls: type[Model], value: Any) -> Model:
        warnings.warn('The `validate` method is deprecated; use `model_validate` instead.', DeprecationWarning)
        return cls.model_validate(value)

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        warnings.warn(
            'The `update_forward_refs` method is deprecated; use `model_rebuild` instead.', DeprecationWarning
        )
        if localns:
            raise TypeError('`localns` arguments are not longer accepted.')
        cls.model_rebuild(force=True)

    def _iter(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn('The private method `_iter` will be removed and should no longer be used.', DeprecationWarning)
        return _deprecated_copy_internals._iter(self, *args, **kwargs)

    def _copy_and_set_values(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method  `_copy_and_set_values` will be removed and should no longer be used.',
            DeprecationWarning,
        )
        return _deprecated_copy_internals._copy_and_set_values(self, *args, **kwargs)

    @classmethod
    def _get_value(cls, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method  `_get_value` will be removed and should no longer be used.', DeprecationWarning
        )
        return _deprecated_copy_internals._get_value(cls, *args, **kwargs)

    def _calculate_keys(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method `_calculate_keys` will be removed and should no longer be used.', DeprecationWarning
        )
        return _deprecated_copy_internals._calculate_keys(self, *args, **kwargs)


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
        namespace['model_config'] = get_config(__config__, __model_name)
    resolved_bases = resolve_bases(__base__)
    meta, ns, kwds = prepare_class(__model_name, resolved_bases, kwds=__cls_kwargs__)
    if resolved_bases is not __base__:
        ns['__orig_bases__'] = __base__
    namespace.update(ns)
    return meta(__model_name, resolved_bases, namespace, __pydantic_reset_parent_namespace__=False, **kwds)


def _collect_bases_data(bases: tuple[type[Any], ...]) -> tuple[set[str], set[str], dict[str, ModelPrivateAttr]]:
    field_names: set[str] = set()
    class_vars: set[str] = set()
    private_attributes: dict[str, ModelPrivateAttr] = {}
    for base in bases:
        if _base_class_defined and issubclass(base, BaseModel) and base != BaseModel:
            # model_fields might not be defined yet in the case of generics, so we use getattr here:
            field_names.update(getattr(base, 'model_fields', {}).keys())
            class_vars.update(base.__class_vars__)
            private_attributes.update(base.__private_attributes__)
    return field_names, class_vars, private_attributes
