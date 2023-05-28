"""
Private logic for creating models.
"""
from __future__ import annotations as _annotations

import typing
import warnings
from abc import ABCMeta
from functools import partial
from types import FunctionType
from typing import Any, Callable, Generic, Mapping

from pydantic_core import SchemaSerializer, SchemaValidator
from typing_extensions import dataclass_transform, deprecated

from ..errors import PydanticErrorCodes, PydanticUndefinedAnnotation, PydanticUserError
from ..fields import Field, FieldInfo, ModelPrivateAttr, PrivateAttr
from ._config import ConfigWrapper
from ._core_utils import flatten_schema_defs, inline_schema_defs
from ._decorators import ComputedFieldInfo, DecoratorInfos, PydanticDescriptorProxy
from ._fields import Undefined, collect_model_fields
from ._generate_schema import GenerateSchema
from ._generics import PydanticGenericMetadata, get_model_typevars_map
from ._schema_generation_shared import CallbackGetCoreSchemaHandler
from ._typing_extra import get_cls_types_namespace, is_classvar, parent_frame_namespace
from ._utils import ClassAttribute, is_valid_identifier

if typing.TYPE_CHECKING:
    from inspect import Signature

    from ..main import BaseModel


IGNORED_TYPES: tuple[Any, ...] = (
    FunctionType,
    property,
    classmethod,
    staticmethod,
    PydanticDescriptorProxy,
    ComputedFieldInfo,
)
object_setattr = object.__setattr__


class _ModelNamespaceDict(dict):  # type: ignore[type-arg]
    """
    A dictionary subclass that intercepts attribute setting on model classes and warns about overriding of decorators.

    Args:
        k (str): The key to be set.
        v (object): The value to set with the key.
    """

    def __setitem__(self, k: str, v: object) -> None:
        existing: Any = self.get(k, None)
        if existing and v is not existing and isinstance(existing, PydanticDescriptorProxy):
            warnings.warn(f'`{k}` overrides an existing Pydantic `{existing.decorator_info.decorator_repr}` decorator')

        return super().__setitem__(k, v)


@dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
class ModelMetaclass(ABCMeta):
    def __new__(
        mcs,
        cls_name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        __pydantic_generic_metadata__: PydanticGenericMetadata | None = None,
        __pydantic_reset_parent_namespace__: bool = True,
        **kwargs: Any,
    ) -> type:
        """Metaclass for creating Pydantic models.

        Args:
            cls_name (str): the name of the class to be created
            bases (tuple[type[Any], ...]]): the base classes of the class to be created
            namespace (dict[str, Any]): the attribute dictionary of the class to be created
            __pydantic_generic_metadata__ (PydanticGenericMetadata | None): metadata for generic models
            __pydantic_reset_parent_namespace__ (bool): reset parent namespace
            **kwargs (Any): catch-all for any other keyword arguments

        Returns:
            type: the new class created by the metaclass
        """
        # Note `ModelMetaclass` refers to `BaseModel`, but is also used to *create* `BaseModel`, so we rely on the fact
        # that `BaseModel` itself won't have any bases, but any subclass of it will, to determine whether the `__new__`
        # call we're in the middle of is for the `BaseModel` class.
        if bases:
            base_field_names, class_vars, base_private_attributes = mcs._collect_bases_data(bases)

            config_wrapper = ConfigWrapper.for_model(bases, namespace, kwargs)
            namespace['model_config'] = config_wrapper.config_dict
            private_attributes = inspect_namespace(
                namespace, config_wrapper.ignored_types, class_vars, base_field_names
            )
            if private_attributes:
                if 'model_post_init' in namespace:
                    # if there are private_attributes and a model_post_init function, we handle both
                    original_model_post_init = namespace['model_post_init']

                    def wrapped_model_post_init(self: BaseModel, __context: Any) -> None:
                        """
                        We need to both initialize private attributes and call the user-defined model_post_init method
                        """
                        init_private_attributes(self, __context)
                        original_model_post_init(self, __context)

                    namespace['model_post_init'] = wrapped_model_post_init
                else:
                    namespace['model_post_init'] = init_private_attributes

            namespace['__class_vars__'] = class_vars
            namespace['__private_attributes__'] = {**base_private_attributes, **private_attributes}

            if config_wrapper.extra == 'allow' or namespace['__private_attributes__']:
                namespace['__getattr__'] = model_extra_private_getattr
            if namespace['__private_attributes__']:
                namespace['__delattr__'] = model_private_delattr

            if '__hash__' not in namespace and config_wrapper.frozen:

                def hash_func(self: Any) -> int:
                    return hash(self.__class__) + hash(tuple(self.__dict__.values()))

                namespace['__hash__'] = hash_func

            cls: type[BaseModel] = super().__new__(mcs, cls_name, bases, namespace, **kwargs)  # type: ignore

            from ..main import BaseModel

            cls.__pydantic_custom_init__ = not getattr(cls.__init__, '__pydantic_base_init__', False)
            cls.__pydantic_post_init__ = None if cls.model_post_init is BaseModel.model_post_init else 'model_post_init'

            cls.__pydantic_decorators__ = DecoratorInfos.build(cls)

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

            cls.__pydantic_complete__ = False  # Ensure this specific class gets completed

            # preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487
            # for attributes not in `new_namespace` (e.g. private attributes)
            for name, obj in private_attributes.items():
                obj.__set_name__(cls, name)

            if __pydantic_reset_parent_namespace__:
                cls.__pydantic_parent_namespace__ = parent_frame_namespace()
            parent_namespace = getattr(cls, '__pydantic_parent_namespace__', None)

            types_namespace = get_cls_types_namespace(cls, parent_namespace)
            set_model_fields(cls, bases, config_wrapper, types_namespace)
            complete_model_class(
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

    def __getattr__(self, item: str) -> Any:
        """
        This is necessary to keep attribute access working for class attribute access
        """
        private_attributes = self.__dict__.get('__private_attributes__')
        if private_attributes and item in private_attributes:
            return private_attributes[item]
        raise AttributeError(item)

    @classmethod
    def __prepare__(cls, *args: Any, **kwargs: Any) -> Mapping[str, object]:
        return _ModelNamespaceDict()

    def __instancecheck__(self, instance: Any) -> bool:
        """
        Avoid calling ABC _abc_subclasscheck unless we're pretty sure.

        See #3829 and python/cpython#92810
        """
        return hasattr(instance, '__pydantic_validator__') and super().__instancecheck__(instance)

    @staticmethod
    def _collect_bases_data(bases: tuple[type[Any], ...]) -> tuple[set[str], set[str], dict[str, ModelPrivateAttr]]:
        from ..main import BaseModel

        field_names: set[str] = set()
        class_vars: set[str] = set()
        private_attributes: dict[str, ModelPrivateAttr] = {}
        for base in bases:
            if issubclass(base, BaseModel) and base is not BaseModel:
                # model_fields might not be defined yet in the case of generics, so we use getattr here:
                field_names.update(getattr(base, 'model_fields', {}).keys())
                class_vars.update(base.__class_vars__)
                private_attributes.update(base.__private_attributes__)
        return field_names, class_vars, private_attributes

    @property
    @deprecated('The `__fields__` attribute is deprecated, use `model_fields` instead.')
    def __fields__(self) -> dict[str, FieldInfo]:
        warnings.warn('The `__fields__` attribute is deprecated, use `model_fields` instead.', DeprecationWarning)
        return self.model_fields


def init_private_attributes(self: BaseModel, __context: Any) -> None:
    """
    This function is meant to behave like a BaseModel method to initialise private attributes.

    It takes context as an argument since that's what pydantic-core passes when calling it.
    """
    pydantic_private = {}
    for name, private_attr in self.__private_attributes__.items():
        default = private_attr.get_default()
        if default is not Undefined:
            pydantic_private[name] = default
    object_setattr(self, '__pydantic_private__', pydantic_private)


def inspect_namespace(  # noqa C901
    namespace: dict[str, Any],
    ignored_types: tuple[type[Any], ...],
    base_class_vars: set[str],
    base_class_fields: set[str],
) -> dict[str, ModelPrivateAttr]:
    """
    iterate over the namespace and:
    * gather private attributes
    * check for items which look like fields but are not (e.g. have no annotation) and warn
    """
    all_ignored_types = ignored_types + IGNORED_TYPES

    private_attributes: dict[str, ModelPrivateAttr] = {}
    raw_annotations = namespace.get('__annotations__', {})

    if '__root__' in raw_annotations or '__root__' in namespace:
        raise TypeError("To define root models, use `pydantic.RootModel` rather than a field called '__root__'")

    ignored_names: set[str] = set()
    for var_name, value in list(namespace.items()):
        if var_name == 'model_config':
            continue
        elif (
            isinstance(value, type)
            and value.__module__ == namespace['__module__']
            and value.__qualname__.startswith(namespace['__qualname__'])
        ):
            # `value` is a nested type defined in this namespace; don't error
            continue
        elif isinstance(value, all_ignored_types) or value.__class__.__module__ == 'functools':
            ignored_names.add(var_name)
            continue
        elif isinstance(value, ModelPrivateAttr):
            if var_name.startswith('__'):
                raise NameError(
                    f'Private attributes "{var_name}" must not have dunder names; '
                    'use a single underscore prefix instead.'
                )
            elif not single_underscore(var_name):
                raise NameError(
                    f'Private attributes "{var_name}" must not be a valid field name; '
                    f'use sunder names, e.g. "_{var_name}"'
                )
            private_attributes[var_name] = value
            del namespace[var_name]
        elif var_name.startswith('__'):
            continue
        elif var_name.startswith('_'):
            if var_name in raw_annotations and not is_classvar(raw_annotations[var_name]):
                private_attributes[var_name] = PrivateAttr(default=value)
                del namespace[var_name]
        elif var_name in base_class_vars:
            continue
        elif var_name not in raw_annotations:
            if var_name in base_class_fields:
                raise PydanticUserError(
                    f'Field {var_name!r} defined on a base class was overridden by a non-annotated attribute. '
                    f'All field definitions, including overrides, require a type annotation.',
                    code='model-field-overridden',
                )
            elif isinstance(value, FieldInfo):
                raise PydanticUserError(
                    f'Field {var_name!r} requires a type annotation', code='model-field-missing-annotation'
                )
            else:
                raise PydanticUserError(
                    f"A non-annotated attribute was detected: `{var_name} = {value!r}`. All model fields require a "
                    f"type annotation; if `{var_name}` is not meant to be a field, you may be able to resolve this "
                    f"error by annotating it as a `ClassVar` or updating `model_config['ignored_types']`.",
                    code='model-field-missing-annotation',
                )

    for ann_name, ann_type in raw_annotations.items():
        if (
            single_underscore(ann_name)
            and ann_name not in private_attributes
            and ann_name not in ignored_names
            and not is_classvar(ann_type)
            and ann_type not in all_ignored_types
            and getattr(ann_type, '__module__', None) != 'functools'
        ):
            private_attributes[ann_name] = PrivateAttr()

    return private_attributes


def single_underscore(name: str) -> bool:
    return name.startswith('_') and not name.startswith('__')


def set_model_fields(
    cls: type[BaseModel], bases: tuple[type[Any], ...], config_wrapper: ConfigWrapper, types_namespace: dict[str, Any]
) -> None:
    """
    Collect and set `cls.model_fields` and `cls.__class_vars__`.
    """
    typevars_map = get_model_typevars_map(cls)
    fields, class_vars = collect_model_fields(cls, bases, config_wrapper, types_namespace, typevars_map=typevars_map)

    cls.model_fields = fields
    cls.__class_vars__.update(class_vars)


def complete_model_class(
    cls: type[BaseModel],
    cls_name: str,
    config_wrapper: ConfigWrapper,
    *,
    raise_errors: bool = True,
    types_namespace: dict[str, Any] | None,
) -> bool:
    """
    Finish building a model class.

    Returns `True` if the model is successfully completed, else `False`.

    This logic must be called after class has been created since validation functions must be bound
    and `get_type_hints` requires a class object.
    """
    typevars_map = get_model_typevars_map(cls)
    gen_schema = GenerateSchema(
        config_wrapper,
        types_namespace,
        typevars_map,
    )
    handler = CallbackGetCoreSchemaHandler(
        partial(gen_schema.generate_schema, from_dunder_get_core_schema=False),
        gen_schema.generate_schema,
    )
    try:
        schema = cls.__get_pydantic_core_schema__(cls, handler)
    except PydanticUndefinedAnnotation as e:
        if raise_errors:
            raise
        undefined_type_error_message = (
            f'`{cls_name}` is not fully defined; you should define `{e.name}`, then call `{cls_name}.model_rebuild()` '
            f'before the first `{cls_name}` instance is created.'
        )

        def attempt_rebuild() -> SchemaValidator | None:
            if cls.model_rebuild(raise_errors=False, _parent_namespace_depth=5):
                return cls.__pydantic_validator__
            else:
                return None

        cls.__pydantic_validator__ = MockValidator(  # type: ignore[assignment]
            undefined_type_error_message, code='class-not-fully-defined', attempt_rebuild=attempt_rebuild
        )
        return False

    core_config = config_wrapper.core_config(cls)

    # debug(schema)
    cls.__pydantic_core_schema__ = schema

    schema = flatten_schema_defs(schema)
    simplified_core_schema = inline_schema_defs(schema)
    cls.__pydantic_validator__ = SchemaValidator(simplified_core_schema, core_config)
    cls.__pydantic_serializer__ = SchemaSerializer(simplified_core_schema, core_config)
    cls.__pydantic_complete__ = True

    # set __signature__ attr only for model class, but not for its instances
    cls.__signature__ = ClassAttribute(
        '__signature__', generate_model_signature(cls.__init__, cls.model_fields, config_wrapper)
    )
    return True


def generate_model_signature(
    init: Callable[..., None], fields: dict[str, FieldInfo], config_wrapper: ConfigWrapper
) -> Signature:
    """
    Generate signature for model based on its fields
    """
    from inspect import Parameter, Signature, signature
    from itertools import islice

    present_params = signature(init).parameters.values()
    merged_params: dict[str, Parameter] = {}
    var_kw = None
    use_var_kw = False

    for param in islice(present_params, 1, None):  # skip self arg
        # inspect does "clever" things to show annotations as strings because we have
        # `from __future__ import annotations` in main, we don't want that
        if param.annotation == 'Any':
            param = param.replace(annotation=Any)
        if param.kind is param.VAR_KEYWORD:
            var_kw = param
            continue
        merged_params[param.name] = param

    if var_kw:  # if custom init has no var_kw, fields which are not declared in it cannot be passed through
        allow_names = config_wrapper.populate_by_name
        for field_name, field in fields.items():
            # when alias is a str it should be used for signature generation
            if isinstance(field.alias, str):
                param_name = field.alias
            else:
                param_name = field_name

            if field_name in merged_params or param_name in merged_params:
                continue

            if not is_valid_identifier(param_name):
                if allow_names and is_valid_identifier(field_name):
                    param_name = field_name
                else:
                    use_var_kw = True
                    continue

            kwargs = {} if field.is_required() else {'default': field.get_default(call_default_factory=False)}
            merged_params[param_name] = Parameter(
                param_name, Parameter.KEYWORD_ONLY, annotation=field.rebuild_annotation(), **kwargs
            )

    if config_wrapper.extra == 'allow':
        use_var_kw = True

    if var_kw and use_var_kw:
        # Make sure the parameter for extra kwargs
        # does not have the same name as a field
        default_model_signature = [
            ('__pydantic_self__', Parameter.POSITIONAL_OR_KEYWORD),
            ('data', Parameter.VAR_KEYWORD),
        ]
        if [(p.name, p.kind) for p in present_params] == default_model_signature:
            # if this is the standard model signature, use extra_data as the extra args name
            var_kw_name = 'extra_data'
        else:
            # else start from var_kw
            var_kw_name = var_kw.name

        # generate a name that's definitely unique
        while var_kw_name in fields:
            var_kw_name += '_'
        merged_params[var_kw_name] = var_kw.replace(name=var_kw_name)

    return Signature(parameters=list(merged_params.values()), return_annotation=None)


class MockValidator:
    """
    Mocker for `pydantic_core.SchemaValidator` which just raises an error when one of its methods is accessed.
    """

    __slots__ = '_error_message', '_code', '_attempt_rebuild'

    def __init__(
        self,
        error_message: str,
        *,
        code: PydanticErrorCodes,
        attempt_rebuild: Callable[[], SchemaValidator | None] | None = None,
    ) -> None:
        """
        Attempt rebuild
        """
        self._error_message = error_message
        self._code: PydanticErrorCodes = code
        self._attempt_rebuild = attempt_rebuild

    def __getattr__(self, item: str) -> None:
        __tracebackhide__ = True
        if self._attempt_rebuild:
            validator = self._attempt_rebuild()
            if validator is not None:
                return getattr(validator, item)

        # raise an AttributeError if `item` doesn't exist
        getattr(SchemaValidator, item)
        raise PydanticUserError(self._error_message, code=self._code)


def model_extra_private_getattr(self: BaseModel, item: str) -> Any:
    """
    This function is used to retrieve unrecognized attribute values from BaseModel subclasses which
    allow (and store) extra and/or private attributes
    """
    if item in self.__private_attributes__:
        attribute = self.__private_attributes__[item]
        if hasattr(attribute, '__get__'):
            return attribute.__get__(self, type(self))  # type: ignore

        try:
            # Note: self.__pydantic_private__ is guaranteed to not be None if self.__private_attributes__ has items
            return self.__pydantic_private__[item]  # type: ignore
        except KeyError as exc:
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
    if self.__pydantic_extra__ is not None:
        try:
            return self.__pydantic_extra__[item]
        except KeyError as exc:
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
    else:
        raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')


def model_private_delattr(self: BaseModel, item: str) -> Any:
    if item in self.__private_attributes__:
        attribute = self.__private_attributes__[item]
        if hasattr(attribute, '__delete__'):
            attribute.__delete__(self)  # type: ignore
            return

        try:
            # Note: self.__pydantic_private__ is guaranteed to not be None if self.__private_attributes__ has items
            del self.__pydantic_private__[item]  # type: ignore
        except KeyError as exc:
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
    elif item in self.model_fields:
        super(self.__class__, self).__delattr__(item)
    else:
        raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
