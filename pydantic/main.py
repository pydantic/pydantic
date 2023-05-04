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
from typing import Any, Callable, Generic, Mapping, Tuple, cast

import pydantic_core
import typing_extensions
from typing_extensions import deprecated

from ._internal import (
    _config,
    _decorators,
    _forward_ref,
    _generics,
    _model_construction,
    _repr,
    _typing_extra,
    _utils,
)
from ._internal._fields import Undefined
from ._migration import getattr_migration
from .config import ConfigDict
from .deprecated import copy_internals as _deprecated_copy_internals
from .deprecated import parse as _deprecated_parse
from .errors import PydanticUndefinedAnnotation, PydanticUserError
from .fields import ComputedFieldInfo, Field, FieldInfo, ModelPrivateAttr
from .json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    GetJsonSchemaHandler,
    JsonSchemaValue,
    model_json_schema,
)

if typing.TYPE_CHECKING:
    from inspect import Signature

    from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator

    from ._internal._utils import AbstractSetIntStr, MappingIntStrAny

    AnyClassMethod = classmethod[Any, Any, Any]
    TupleGenerator = typing.Generator[Tuple[str, Any], None, None]
    Model = typing.TypeVar('Model', bound='BaseModel')
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx: typing_extensions.TypeAlias = 'set[int] | set[str] | dict[int, Any] | dict[str, Any] | None'

__all__ = 'BaseModel', 'create_model'

_object_setattr = _model_construction.object_setattr
# Note `ModelMetaclass` refers to `BaseModel`, but is also used to *create* `BaseModel`, so we need to add this extra
# (somewhat hacky) boolean to keep track of whether we've created the `BaseModel` class yet, and therefore whether it's
# safe to refer to it. If it *hasn't* been created, we assume that the `__new__` call we're in the middle of is for
# the `BaseModel` class, since that's defined immediately after the metaclass.
_base_class_defined = False


class _ModelNamespaceDict(dict):  # type: ignore[type-arg]
    """
    Intercept attributes being set on model classes and warn about overriding of decorators (`@field_validator`, etc.)
    """

    def __setitem__(self, k: str, v: object) -> None:
        existing: Any = self.get(k, None)
        if existing and v is not existing and isinstance(existing, _decorators.PydanticDescriptorProxy):
            warnings.warn(f'`{k}` overrides an existing Pydantic `{existing.decorator_info.decorator_repr}` decorator')

        return super().__setitem__(k, v)


@typing_extensions.dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
class ModelMetaclass(ABCMeta):
    def __new__(
        mcs,
        cls_name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        __pydantic_generic_metadata__: _generics.PydanticGenericMetadata | None = None,
        __pydantic_reset_parent_namespace__: bool = True,
        **kwargs: Any,
    ) -> type:
        if _base_class_defined:
            base_field_names, class_vars, base_private_attributes = _collect_bases_data(bases)

            config_wrapper = _config.ConfigWrapper.for_model(bases, namespace, kwargs)
            namespace['model_config'] = config_wrapper.config_dict
            private_attributes = _model_construction.inspect_namespace(
                namespace, config_wrapper.ignored_types, class_vars, base_field_names
            )
            if private_attributes:
                slots: set[str] = set(namespace.get('__slots__', ()))
                namespace['__slots__'] = slots | private_attributes.keys()

                if 'model_post_init' in namespace:
                    # if there are private_attributes and a model_post_init function, we handle both
                    original_model_post_init = namespace['model_post_init']

                    def wrapped_model_post_init(self: BaseModel, __context: Any) -> None:
                        """
                        We need to both initialize private attributes and call the user-defined model_post_init method
                        """
                        _model_construction.init_private_attributes(self, __context)
                        original_model_post_init(self, __context)

                    namespace['model_post_init'] = wrapped_model_post_init
                else:
                    namespace['model_post_init'] = _model_construction.init_private_attributes

            namespace['__class_vars__'] = class_vars
            namespace['__private_attributes__'] = {**base_private_attributes, **private_attributes}

            if config_wrapper.extra == 'allow':
                namespace['__getattr__'] = _model_construction.model_extra_getattr

            if '__hash__' not in namespace and config_wrapper.frozen:

                def hash_func(self: Any) -> int:
                    return hash(self.__class__) + hash(tuple(self.__dict__.values()))

                namespace['__hash__'] = hash_func

            cls: type[BaseModel] = super().__new__(mcs, cls_name, bases, namespace, **kwargs)  # type: ignore

            cls.__pydantic_decorators__ = _decorators.DecoratorInfos.build(cls)

            # Use the getattr below to grab the __parameters__ from the `typing.Generic` parent class
            if __pydantic_generic_metadata__:
                cls.__pydantic_generic_metadata__ = __pydantic_generic_metadata__
            else:
                parameters = getattr(cls, '__parameters__', ())
                parent_parameters = getattr(cls, '__pydantic_generic_metadata__', {}).get('parameters', ())
                if parameters and parent_parameters and not all(x in parameters for x in parent_parameters):
                    combined_parameters = parent_parameters + tuple(x for x in parameters if x not in parent_parameters)
                    parameters_str = ', '.join([str(x) for x in combined_parameters])
                    error_message = (
                        f'All parameters must be present on typing.Generic;'
                        f' you should inherit from typing.Generic[{parameters_str}]'
                    )
                    if Generic not in bases:  # pragma: no cover
                        # This branch will only be hit if I have misunderstood how `__parameters__` works.
                        # If that is the case, and a user hits this, I could imagine it being very helpful
                        # to have this extra detail in the reported traceback.
                        error_message += f' (bases={bases})'
                    raise TypeError(error_message)

                cls.__pydantic_generic_metadata__ = {
                    'origin': None,
                    'args': (),
                    'parameters': parameters,
                }

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

            types_namespace = _typing_extra.get_cls_types_namespace(cls, parent_namespace)
            _model_construction.set_model_fields(cls, bases, types_namespace)
            _model_construction.complete_model_class(
                cls,
                cls_name,
                config_wrapper,
                raise_errors=False,
                types_namespace=types_namespace,
            )
            # using super(cls, cls) on the next line ensures we only call the parent class's __pydantic_init_subclass__
            # I believe the `type: ignore` is only necessary because mypy doesn't realize that this code branch is
            # only hit for _proper_ subclasses of BaseModel
            super(cls, cls).__pydantic_init_subclass__(**kwargs)  # type: ignore[misc]
            return cls
        else:
            # this is the BaseModel class itself being created, no logic required
            return super().__new__(mcs, cls_name, bases, namespace, **kwargs)

    @classmethod
    def __prepare__(cls, *args: Any, **kwargs: Any) -> Mapping[str, object]:
        return _ModelNamespaceDict()

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
        __pydantic_fields_set__: set[str] = set()
        __pydantic_extra__: dict[str, Any] | None = None
        __pydantic_generic_metadata__: typing.ClassVar[_generics.PydanticGenericMetadata]
        __pydantic_parent_namespace__: typing.ClassVar[dict[str, Any] | None]
    else:
        # `model_fields` and `__pydantic_decorators__` must be set for
        # pydantic._internal._generate_schema.GenerateSchema.model_schema to work for a plain BaseModel annotation
        model_fields = {}
        __pydantic_decorators__ = _decorators.DecoratorInfos()
        __pydantic_validator__ = _model_construction.MockValidator(
            'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly',
            code='base-model-instantiated',
        )

    model_config = ConfigDict()
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__'
    __doc__ = ''  # Null out the Representation docstring
    __pydantic_model_complete__ = False

    def __init__(__pydantic_self__, **data: Any) -> None:  # type: ignore
        """
        Create a new model by parsing and validating input data from keyword arguments.

        Raises ValidationError if the input data cannot be parsed to form a valid model.

        Uses something other than `self` for the first arg to allow "self" as a field name.
        """
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        __pydantic_self__.__pydantic_validator__.validate_python(data, self_instance=__pydantic_self__)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, __source: type[BaseModel], __handler: Callable[[Any], CoreSchema]
    ) -> CoreSchema:
        """Hook into generating the model's CoreSchema.

        Args:
            __source (type[BaseModel]): The class we are generating a schema for.
                This will generally be the same as the `cls` argument if this is a classmethod.
            __handler (GetJsonSchemaHandler): Call into Pydantic's internal JSON schema generation.
                A callable that calls into Pydantic's internal CoreSchema generation logic.

        Returns:
            CoreSchema: A `pydantic-core` `CoreSchema`.
        """
        # Only use the cached value from this _exact_ class; we don't want one from a parent class
        # This is why we check `cls.__dict__` and don't use `cls.__pydantic_core_schema__` or similar.
        if '__pydantic_core_schema__' in cls.__dict__:
            # Due to the way generic classes are built, it's possible that an invalid schema may be temporarily
            # set on generic classes. I think we could resolve this to ensure that we get proper schema caching
            # for generics, but for simplicity for now, we just always rebuild if the class has a generic origin.
            if not cls.__pydantic_generic_metadata__['origin']:
                return cls.__pydantic_core_schema__

        return __handler(__source)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        __core_schema: CoreSchema,
        __handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """Hook into generating the model's JSON schema.

        Args:
            __core_schema (CoreSchema): A `pydantic-core` CoreSchema.
                You can ignore this argument and call the handler with a new CoreSchema,
                wrap this CoreSchema (`{'type': 'nullable', 'schema': current_schema}`),
                or just call the handler with the original schema.
            __handler (GetJsonSchemaHandler): Call into Pydantic's internal JSON schema generation.
                This will raise a `pydantic.errors.PydanticInvalidForJsonSchema` if JSON schema
                generation fails.
                Since this gets called by `BaseModel.model_json_schema` you can override the
                `schema_generator` argument to that function to change JSON schema generation globally
                for a type.

        Returns:
            JsonSchemaValue: A JSON schema, as a Python object.
        """
        return __handler(__core_schema)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        This is intended to behave just like `__init_subclass__`, but is called by ModelMetaclass
        only after the class is actually fully initialized. In particular, attributes like `model_fields` will
        be present when this is called.

        This is necessary because `__init_subclass__` will always be called by `type.__new__`,
        and it would require a prohibitively large refactor to the `ModelMetaclass` to ensure that
        `type.__new__` was called in such a manner that the class would already be sufficiently initialized.

        This will receive the same `kwargs` that would be passed to the standard `__init_subclass__`, namely,
        any kwargs passed to the class definition that aren't used internally by pydantic.
        """
        pass

    @classmethod
    def model_validate(
        cls: type[Model], obj: Any, *, strict: bool | None = None, context: dict[str, Any] | None = None
    ) -> Model:
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return cls.__pydantic_validator__.validate_python(obj, strict=strict, context=context)

    @property
    def model_fields_set(self) -> set[str]:
        """
        The set of fields that have been set on this model instance, i.e. that were not filled from defaults.
        """
        return self.__pydantic_fields_set__

    @property
    def model_extra(self) -> dict[str, Any] | None:
        """
        Extra fields set during validation, this will be `None` if `config.extra` is not set to `"allow"`.
        """
        return self.__pydantic_extra__

    @property
    def model_computed_fields(self) -> dict[str, ComputedFieldInfo]:
        """
        The computed fields of this model instance.
        """
        return {k: v.info for k, v in self.__pydantic_decorators__.computed_fields.items()}

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

    def model_post_init(self, __context: Any) -> None:
        """
        If you override `model_post_init`, it will be called at the end of `__init__` and `model_construct`
        """
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__class_vars__:
            raise AttributeError(
                f'"{name}" is a ClassVar of `{self.__class__.__name__}` and cannot be set on an instance. '
                f'If you want to set a value on the class, use `{self.__class__.__name__}.{name} = value`.'
            )
        elif name.startswith('_'):
            _object_setattr(self, name, value)
            return
        elif self.model_config.get('frozen', None):
            raise TypeError(f'"{self.__class__.__name__}" is frozen and does not support item assignment')

        attr = getattr(self.__class__, name, None)
        if isinstance(attr, property):
            attr.__set__(self, value)
        elif self.model_config.get('validate_assignment', None):
            self.__pydantic_validator__.validate_assignment(self, name, value)
        elif self.model_config.get('extra') != 'allow' and name not in self.model_fields:
            # TODO - matching error
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        else:
            self.__dict__[name] = value
            self.__pydantic_fields_set__.add(name)

    def __getstate__(self) -> dict[Any, Any]:
        private_attrs = ((k, getattr(self, k, Undefined)) for k in self.__private_attributes__)
        return {
            '__dict__': self.__dict__,
            '__pydantic_fields_set__': self.__pydantic_fields_set__,
            '__private_attribute_values__': {k: v for k, v in private_attrs if v is not Undefined},
        }

    def __setstate__(self, state: dict[Any, Any]) -> None:
        _object_setattr(self, '__dict__', state['__dict__'])
        _object_setattr(self, '__pydantic_fields_set__', state['__pydantic_fields_set__'])
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
        Creates a new model setting __dict__ and __pydantic_fields_set__ from trusted or pre-validated data.
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
        _extra: dict[str, Any] | None = None
        if cls.model_config.get('extra') == 'allow':
            _extra = {}
            for k, v in values.items():
                if k in cls.model_fields:
                    fields_values[k] = v
                else:
                    _extra[k] = v
        else:
            fields_values.update(values)
        _object_setattr(m, '__dict__', fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        _object_setattr(m, '__pydantic_fields_set__', _fields_set)
        _object_setattr(m, '__pydantic_extra__', _extra)
        if type(m).model_post_init is not BaseModel.model_post_init:
            m.model_post_init(None)
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
        metadata = {'title': cls.model_config.get('title', None) or cls.__name__, 'description': getdoc(cls) or None}
        metadata = {k: v for k, v in metadata.items() if v is not None}
        return {**metadata, **json_schema}

    @classmethod
    def model_rebuild(
        cls,
        *,
        force: bool = False,
        raise_errors: bool = True,
        _parent_namespace_depth: int = 2,
        _types_namespace: dict[str, Any] | None = None,
    ) -> bool | None:
        """
        Try to (Re)construct the model schema.
        """
        if not force and cls.__pydantic_model_complete__:
            return None
        else:
            if _types_namespace is not None:
                types_namespace: dict[str, Any] | None = _types_namespace.copy()
            else:
                if _parent_namespace_depth > 0:
                    frame_parent_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth) or {}
                    cls_parent_ns = cls.__pydantic_parent_namespace__ or {}
                    cls.__pydantic_parent_namespace__ = {**cls_parent_ns, **frame_parent_ns}

                types_namespace = cls.__pydantic_parent_namespace__

                types_namespace = _typing_extra.get_cls_types_namespace(cls, types_namespace)
            return _model_construction.complete_model_class(
                cls,
                cls.__name__,
                _config.ConfigWrapper(cls.model_config, check=False),
                raise_errors=raise_errors,
                types_namespace=types_namespace,
            )

    def __iter__(self) -> TupleGenerator:
        """
        so `dict(model)` works
        """
        yield from self.__dict__.items()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseModel):
            # When comparing instances of generic types for equality, as long as all field values are equal,
            # only require their generic origin types to be equal, rather than exact type equality.
            # This prevents headaches like MyGeneric(x=1) != MyGeneric[Any](x=1).
            self_type = self.__pydantic_generic_metadata__['origin'] or self.__class__
            other_type = other.__pydantic_generic_metadata__['origin'] or other.__class__

            if self_type != other_type:
                return False

            if self.__dict__ != other.__dict__:
                return False

            # If the types and field values match, check for equality of private attributes
            for k in self.__private_attributes__:
                if getattr(self, k, Undefined) != getattr(other, k, Undefined):
                    return False

            return True
        else:
            return NotImplemented  # delegate to the other item in the comparison

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
            if self.model_config.get('extra') == 'allow':
                for k, v in update.items():
                    if k in self.model_fields:
                        copied.__dict__[k] = v
                    else:
                        if copied.__pydantic_extra__ is None:
                            copied.__pydantic_extra__ = {}
                        copied.__pydantic_extra__[k] = v
            else:
                copied.__dict__.update(update)
            copied.__pydantic_fields_set__.update(update.keys())
        return copied

    def __copy__(self: Model) -> Model:
        """
        Returns a shallow copy of the model
        """
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', copy(self.__dict__))
        _object_setattr(m, '__pydantic_extra__', copy(self.__pydantic_extra__))
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))
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
        _object_setattr(m, '__pydantic_extra__', deepcopy(self.__pydantic_extra__, memo=memo))
        # This next line doesn't need a deepcopy because __pydantic_fields_set__ is a set[str],
        # and attempting a deepcopy would be marginally slower.
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))
        for name in self.__private_attributes__:
            value = getattr(self, name, Undefined)
            if value is not Undefined:
                _object_setattr(m, name, deepcopy(value, memo=memo))
        return m

    def __repr_args__(self) -> _repr.ReprArgs:
        yield from (
            (k, v)
            for k, v in self.__dict__.items()
            if not k.startswith('_') and (k not in self.model_fields or self.model_fields[k].repr)
        )
        pydantic_extra = self.__pydantic_extra__
        if pydantic_extra is not None:
            yield from ((k, v) for k, v in pydantic_extra.items())
        yield from ((k, getattr(self, k)) for k, v in self.model_computed_fields.items() if v.repr)

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
        if not cls.__pydantic_generic_metadata__['parameters'] and Generic not in cls.__bases__:
            raise TypeError(f'{cls} is not a generic class')

        if not isinstance(typevar_values, tuple):
            typevar_values = (typevar_values,)
        _generics.check_parameters_count(cls, typevar_values)

        # Build map from generic typevars to passed params
        typevars_map: dict[_typing_extra.TypeVarType, type[Any]] = dict(
            zip(cls.__pydantic_generic_metadata__['parameters'], typevar_values)
        )

        if _utils.all_identical(typevars_map.keys(), typevars_map.values()) and typevars_map:
            submodel = cls  # if arguments are equal to parameters it's the same object
            _generics.set_cached_generic_type(cls, typevar_values, submodel)
        else:
            parent_args = cls.__pydantic_generic_metadata__['args']
            if not parent_args:
                args = typevar_values
            else:
                args = tuple(_generics.replace_types(arg, typevars_map) for arg in parent_args)

            origin = cls.__pydantic_generic_metadata__['origin'] or cls
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
    @property
    @deprecated('The `__fields_set__` attribute is deprecated, use `model_fields_set` instead.')
    def __fields_set__(self) -> set[str]:
        warnings.warn(
            'The `__fields_set__` attribute is deprecated, use `model_fields_set` instead.', DeprecationWarning
        )
        return self.__pydantic_fields_set__

    @deprecated('The `dict` method is deprecated; use `model_dump` instead.')
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

    @deprecated('The `json` method is deprecated; use `model_dump_json` instead.')
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
    @deprecated('The `parse_obj` method is deprecated; use `model_validate` instead.')
    def parse_obj(cls: type[Model], obj: Any) -> Model:
        warnings.warn('The `parse_obj` method is deprecated; use `model_validate` instead.', DeprecationWarning)
        return cls.model_validate(obj)

    @classmethod
    @deprecated(
        'The `parse_raw` method is deprecated; if your data is JSON use `model_validate_json`, '
        'otherwise load the data then use `model_validate` instead.'
    )
    def parse_raw(
        cls: type[Model],
        b: str | bytes,
        *,
        content_type: str | None = None,
        encoding: str = 'utf8',
        proto: _deprecated_parse.Protocol | None = None,
        allow_pickle: bool = False,
    ) -> Model:
        warnings.warn(
            'The `parse_raw` method is deprecated; if your data is JSON use `model_validate_json`, '
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
                # The type: ignore on the next line is to ignore the requirement of LiteralString
                'type': pydantic_core.PydanticCustomError(type_str, str(exc)),  # type: ignore
                'loc': ('__root__',),
                'input': b,
            }
            raise pydantic_core.ValidationError(cls.__name__, [error])
        return cls.model_validate(obj)

    @classmethod
    @deprecated(
        'The `parse_file` method is deprecated; load the data from file, then if your data is JSON '
        'use `model_json_validate` otherwise `model_validate` instead.'
    )
    def parse_file(
        cls: type[Model],
        path: str | Path,
        *,
        content_type: str | None = None,
        encoding: str = 'utf8',
        proto: _deprecated_parse.Protocol | None = None,
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
    # @deprecated(
    #     "The `from_orm` method is deprecated; set "
    #     "`model_config['from_attributes']=True` and use `model_validate` instead."
    # )
    def from_orm(cls: type[Model], obj: Any) -> Model:
        warnings.warn(
            'The `from_orm` method is deprecated; set `model_config["from_attributes"]=True` '
            'and use `model_validate` instead.',
            DeprecationWarning,
        )
        if not cls.model_config.get('from_attributes', None):
            raise PydanticUserError(
                'You must set the config attribute `from_attributes=True` to use from_orm', code=None
            )
        return cls.model_validate(obj)

    @classmethod
    @deprecated('The `construct` method is deprecated; use `model_construct` instead.')
    def construct(cls: type[Model], _fields_set: set[str] | None = None, **values: Any) -> Model:
        warnings.warn('The `construct` method is deprecated; use `model_construct` instead.', DeprecationWarning)
        return cls.model_construct(_fields_set=_fields_set, **values)

    @deprecated('The copy method is deprecated; use `model_copy` instead.')
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
            _deprecated_copy_internals._iter(  # type: ignore
                self, to_dict=False, by_alias=False, include=include, exclude=exclude, exclude_unset=False
            ),
            **(update or {}),
        )
        if self.__pydantic_extra__ is None:
            extra: dict[str, Any] | None = None
        else:
            extra = self.__pydantic_extra__.copy()
            for k in list(self.__pydantic_extra__):
                if k not in values:  # k was in the exclude
                    extra.pop(k)
            for k in list(values):
                if k in self.__pydantic_extra__:  # k must have come from extra
                    extra[k] = values.pop(k)

        # new `__pydantic_fields_set__` can have unset optional fields with a set value in `update` kwarg
        if update:
            fields_set = self.__pydantic_fields_set__ | update.keys()
        else:
            fields_set = set(self.__pydantic_fields_set__)

        # removing excluded fields from `__pydantic_fields_set__`
        if exclude:
            fields_set -= set(exclude)

        return _deprecated_copy_internals._copy_and_set_values(self, values, fields_set, extra, deep=deep)

    @classmethod
    @deprecated('The `schema` method is deprecated; use `model_json_schema` instead.')
    def schema(
        cls, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE
    ) -> typing.Dict[str, Any]:  # noqa UP006
        warnings.warn('The `schema` method is deprecated; use `model_json_schema` instead.', DeprecationWarning)
        return cls.model_json_schema(by_alias=by_alias, ref_template=ref_template)

    @classmethod
    @deprecated('The `schema_json` method is deprecated; use `model_json_schema` and json.dumps instead.')
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
    @deprecated('The `validate` method is deprecated; use `model_validate` instead.')
    def validate(cls: type[Model], value: Any) -> Model:
        warnings.warn('The `validate` method is deprecated; use `model_validate` instead.', DeprecationWarning)
        return cls.model_validate(value)

    @classmethod
    @deprecated('The `update_forward_refs` method is deprecated; use `model_rebuild` instead.')
    def update_forward_refs(cls, **localns: Any) -> None:
        warnings.warn(
            'The `update_forward_refs` method is deprecated; use `model_rebuild` instead.', DeprecationWarning
        )
        if localns:
            raise TypeError('`localns` arguments are not longer accepted.')
        cls.model_rebuild(force=True)

    @deprecated('The private method `_iter` will be removed and should no longer be used.')
    def _iter(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn('The private method `_iter` will be removed and should no longer be used.', DeprecationWarning)
        return _deprecated_copy_internals._iter(self, *args, **kwargs)  # type: ignore

    @deprecated('The private method `_calculate_keys` will be removed and should no longer be used.')
    def _copy_and_set_values(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method  `_copy_and_set_values` will be removed and should no longer be used.',
            DeprecationWarning,
        )
        return _deprecated_copy_internals._copy_and_set_values(self, *args, **kwargs)  # type: ignore

    @classmethod
    @deprecated('The private method `_get_value` will be removed and should no longer be used.')
    def _get_value(cls, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method  `_get_value` will be removed and should no longer be used.', DeprecationWarning
        )
        return _deprecated_copy_internals._get_value(cls, *args, **kwargs)  # type: ignore

    @deprecated('The private method `_calculate_keys` will be removed and should no longer be used.')
    def _calculate_keys(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method `_calculate_keys` will be removed and should no longer be used.', DeprecationWarning
        )
        return _deprecated_copy_internals._calculate_keys(self, *args, **kwargs)  # type: ignore


_base_class_defined = True


@typing.overload
def create_model(
    __model_name: str,
    *,
    __config__: ConfigDict | None = None,
    __base__: None = None,
    __module__: str = __name__,
    __validators__: dict[str, AnyClassMethod] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    **field_definitions: Any,
) -> type[BaseModel]:
    ...


@typing.overload
def create_model(
    __model_name: str,
    *,
    __config__: ConfigDict | None = None,
    __base__: type[Model] | tuple[type[Model], ...],
    __module__: str = __name__,
    __validators__: dict[str, AnyClassMethod] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    **field_definitions: Any,
) -> type[Model]:
    ...


def create_model(
    __model_name: str,
    *,
    __config__: ConfigDict | None = None,
    __base__: type[Model] | tuple[type[Model], ...] | None = None,
    __module__: str = __name__,
    __validators__: dict[str, AnyClassMethod] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
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
            raise PydanticUserError(
                'to avoid confusion `__config__` and `__base__` cannot be used together',
                code='create-model-config-base',
            )
        if not isinstance(__base__, tuple):
            __base__ = (__base__,)
    else:
        __base__ = (cast(typing.Type['Model'], BaseModel),)

    __cls_kwargs__ = __cls_kwargs__ or {}

    fields = {}
    annotations = {}

    for f_name, f_def in field_definitions.items():
        if f_name.startswith('_'):
            warnings.warn(f'fields may not start with an underscore, ignoring "{f_name}"', RuntimeWarning)
        if isinstance(f_def, tuple):
            f_def = cast('tuple[str, Any]', f_def)
            try:
                f_annotation, f_value = f_def
            except ValueError as e:
                raise PydanticUserError(
                    'Field definitions should either be a `(<type>, <default>)`.',
                    code='create-model-field-definitions',
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
        namespace['model_config'] = _config.ConfigWrapper(__config__).config_dict
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


__getattr__ = getattr_migration(__name__)
