"""
Defining fields on models.
"""
from __future__ import annotations as _annotations

import dataclasses
import inspect
import sys
import typing
from copy import copy
from dataclasses import Field as DataclassField
from typing import Any
from warnings import warn

import annotated_types
import typing_extensions

from . import types
from ._internal import _decorators, _fields, _forward_ref, _internal_dataclass, _repr, _typing_extra, _utils
from ._internal._fields import Undefined
from ._internal._generics import replace_types
from .errors import PydanticUserError

if typing.TYPE_CHECKING:
    from pydantic_core import core_schema as _core_schema

    from ._internal._repr import ReprArgs


class FieldInfo(_repr.Representation):
    """
    Hold information about a field.

    FieldInfo is used for any field definition whether or not the `Field()` function is explicitly used.

    Attributes:
        annotation (type): The type annotation of the field.
        default (Any): The default value of the field.
        default_factory (callable): The factory function used to construct the default value of the field.
        alias (str): The alias name of the field.
        alias_priority (int): The priority of the field's alias.
        validation_alias (str): The validation alias name of the field.
        serialization_alias (str): The serialization alias name of the field.
        title (str): The title of the field.
        description (str): The description of the field.
        examples (List[str]): List of examples of the field.
        exclude (bool): Whether or not to exclude the field from the model schema.
        include (bool): Whether or not to include the field in the model schema.
        metadata (Dict[str, Any]): Dictionary of metadata constraints.
        repr (bool): Whether or not to include the field in representation of the model.
        discriminator (bool): Whether or not to include the field in the "discriminator" schema property of the model.
        json_schema_extra (Dict[str, Any]): Dictionary of extra JSON schema properties.
        init_var (bool): Whether or not the field should be included in the constructor of the model.
        kw_only (bool): Whether or not the field should be a keyword-only argument in the constructor of the model.
        validate_default (bool): Whether or not to validate the default value of the field.
        frozen (bool): Whether or not the field is frozen.
        final (bool): Whether or not the field is final.
    """

    # TODO: Need to add attribute annotations

    __slots__ = (
        'annotation',
        'default',
        'default_factory',
        'alias',
        'alias_priority',
        'validation_alias',
        'serialization_alias',
        'title',
        'description',
        'examples',
        'exclude',
        'include',
        'metadata',
        'repr',
        'discriminator',
        'json_schema_extra',
        'init_var',
        'kw_only',
        'validate_default',
        'frozen',
        'final',
    )

    # used to convert kwargs to metadata/constraints,
    # None has a special meaning - these items are collected into a `PydanticGeneralMetadata`
    metadata_lookup: dict[str, typing.Callable[[Any], Any] | None] = {
        'gt': annotated_types.Gt,
        'ge': annotated_types.Ge,
        'lt': annotated_types.Lt,
        'le': annotated_types.Le,
        'multiple_of': annotated_types.MultipleOf,
        'strict': types.Strict,
        'min_length': annotated_types.MinLen,
        'max_length': annotated_types.MaxLen,
        'pattern': None,
        'allow_inf_nan': None,
        'max_digits': None,
        'decimal_places': None,
    }

    def __init__(self, **kwargs: Any) -> None:
        # TODO: This is a good place to add migration warnings; we should use overload for type-hinting the signature
        self.annotation, annotation_metadata = self._extract_metadata(kwargs.get('annotation'))

        default = kwargs.pop('default', Undefined)
        if default is Ellipsis:
            self.default = Undefined
        else:
            self.default = default

        self.default_factory = kwargs.get('default_factory')

        if self.default is not Undefined and self.default_factory is not None:
            raise TypeError('cannot specify both default and default_factory')

        self.alias = kwargs.get('alias')
        self.alias_priority = kwargs.get('alias_priority') or 2 if self.alias is not None else None
        self.title = kwargs.get('title')
        self.validation_alias = kwargs.get('validation_alias', None)
        self.serialization_alias = kwargs.get('serialization_alias', None)
        self.description = kwargs.get('description')
        self.examples = kwargs.get('examples')
        self.exclude = kwargs.get('exclude')
        self.include = kwargs.get('include')
        self.metadata = self._collect_metadata(kwargs) + annotation_metadata
        self.discriminator = kwargs.get('discriminator')
        self.repr = kwargs.get('repr', True)
        self.json_schema_extra = kwargs.get('json_schema_extra')
        self.validate_default = kwargs.get('validate_default', None)
        self.frozen = kwargs.get('frozen', None)
        self.final = kwargs.get('final', None)
        # currently only used on dataclasses
        self.init_var = kwargs.get('init_var', None)
        self.kw_only = kwargs.get('kw_only', None)

    @classmethod
    def from_field(cls, default: Any = Undefined, **kwargs: Any) -> FieldInfo:
        """
        Create a new `FieldInfo` object with the `Field` function.

        Args:
            default (Any): The default value for the field. Defaults to Undefined.
            **kwargs: Additional arguments dictionary.

        Raises:
            TypeError: If 'annotation' is passed as a keyword argument.

        Returns:
            FieldInfo: A new FieldInfo object with the given parameters.

        Examples:
            This is how you can create a field with default value like this:

            ```python
            import pydantic

            class MyModel(pydantic.BaseModel):
                foo: int = pydantic.Field(4, ...)
            ```
        """
        # TODO: This is a good place to add migration warnings; should we use overload for type-hinting the signature?
        if 'annotation' in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        return cls(default=default, **kwargs)

    @classmethod
    def from_annotation(cls, annotation: type[Any] | _forward_ref.PydanticForwardRef) -> FieldInfo:
        """
        Creates a `FieldInfo` instance from a bare annotation.

        Args:
            annotation (Union[type[Any], _forward_ref.PydanticForwardRef]): An annotation object.

        Returns:
            FieldInfo: An instance of the field metadata.

        Examples:
            This is how you can create a field from a bare annotation like this:

            ```python
            import pydantic
            class MyModel(pydantic.BaseModel):
                foo: int  # <-- like this
            ```

            We also account for the case where the annotation can be an instance of `Annotated` and where
            one of the (not first) arguments in `Annotated` are an instance of `FieldInfo`, e.g.:

            ```python
            import pydantic, annotated_types, typing

            class MyModel(pydantic.BaseModel):
                foo: typing.Annotated[int, annotated_types.Gt(42)]
                bar: typing.Annotated[int, Field(gt=42)]
            ```

        """
        final = False
        if _typing_extra.is_finalvar(annotation):
            final = True
            if annotation is not typing_extensions.Final:
                annotation = typing_extensions.get_args(annotation)[0]

        if _typing_extra.is_annotated(annotation):
            first_arg, *extra_args = typing_extensions.get_args(annotation)
            if _typing_extra.is_finalvar(first_arg):
                final = True
            field_info = cls._find_field_info_arg(extra_args)
            if field_info:
                new_field_info = copy(field_info)
                new_field_info.annotation = first_arg
                new_field_info.final = final
                new_field_info.metadata += [a for a in extra_args if not isinstance(a, FieldInfo)]
                return new_field_info

        return cls(annotation=annotation, final=final)

    @classmethod
    def from_annotated_attribute(cls, annotation: type[Any], default: Any) -> FieldInfo:
        """
        Create `FieldInfo` from an annotation with a default value.

        Args:
            annotation (type[Any]): The type annotation of the field.
            default (Any): The default value of the field.

        Returns:
            FieldInfo: A field object with the passed values.

        Examples:
        ```python
        import pydantic, annotated_types, typing

        class MyModel(pydantic.BaseModel):
            foo: int = 4  # <-- like this
            bar: typing.Annotated[int, annotated_types.Gt(4)] = 4  # <-- or this
            spam: typing.Annotated[int, pydantic.Field(gt=4)] = 4  # <-- or this
        ```
        """
        final = False
        if _typing_extra.is_finalvar(annotation):
            final = True
            if annotation is not typing_extensions.Final:
                annotation = typing_extensions.get_args(annotation)[0]

        if isinstance(default, cls):
            default.annotation, annotation_metadata = cls._extract_metadata(annotation)
            default.metadata += annotation_metadata
            default.final = final
            return default
        elif isinstance(default, dataclasses.Field):
            init_var = False
            if annotation is dataclasses.InitVar:
                if sys.version_info < (3, 8):
                    raise RuntimeError('InitVar is not supported in Python 3.7 as type information is lost')

                init_var = True
                annotation = Any
            elif isinstance(annotation, dataclasses.InitVar):
                init_var = True
                annotation = annotation.type
            pydantic_field = cls._from_dataclass_field(default)
            pydantic_field.annotation, annotation_metadata = cls._extract_metadata(annotation)
            pydantic_field.metadata += annotation_metadata
            pydantic_field.final = final
            pydantic_field.init_var = init_var
            pydantic_field.kw_only = getattr(default, 'kw_only', None)
            return pydantic_field
        else:
            if _typing_extra.is_annotated(annotation):
                first_arg, *extra_args = typing_extensions.get_args(annotation)
                field_info = cls._find_field_info_arg(extra_args)
                if field_info is not None:
                    if not field_info.is_required():
                        raise TypeError('Default may not be specified twice on the same field')
                    new_field_info = copy(field_info)
                    new_field_info.default = default
                    new_field_info.annotation = first_arg
                    new_field_info.metadata += [a for a in extra_args if not isinstance(a, FieldInfo)]
                    return new_field_info

            return cls(annotation=annotation, default=default, final=final)

    @classmethod
    def _from_dataclass_field(cls, dc_field: DataclassField[Any]) -> FieldInfo:
        """
        Return a new `FieldInfo` instance from a `dataclasses.Field` instance.

        Args:
            dc_field (dataclasses.Field): The `dataclasses.Field` instance to convert.

        Returns:
            FieldInfo: The corresponding `FieldInfo` instance.

        Raises:
            TypeError: If any of the `FieldInfo` kwargs does not match the `dataclass.Field` kwargs.
        """
        default = dc_field.default
        if default is dataclasses.MISSING:
            default = Undefined

        if dc_field.default_factory is dataclasses.MISSING:
            default_factory: typing.Callable[[], Any] | None = None
        else:
            default_factory = dc_field.default_factory

        # use the `Field` function so in correct kwargs raise the correct `TypeError`
        field = Field(default=default, default_factory=default_factory, repr=dc_field.repr, **dc_field.metadata)

        field.annotation, annotation_metadata = cls._extract_metadata(dc_field.type)
        field.metadata += annotation_metadata
        return field

    @classmethod
    def _extract_metadata(cls, annotation: type[Any] | None) -> tuple[type[Any] | None, list[Any]]:
        """Tries to extract metadata/constraints from an annotation if it uses `Annotated`.

        Args:
            annotation (type[Any] | None): The type hint annotation for which metadata has to be extracted.

        Returns:
            tuple[type[Any] | None, list[Any]]: A tuple containing the extracted metadata type and the list
            of extra arguments.

        Raises:
            TypeError: If a `Field` is used twice on the same field.
        """
        if annotation is not None:
            if _typing_extra.is_annotated(annotation):
                first_arg, *extra_args = typing_extensions.get_args(annotation)
                if cls._find_field_info_arg(extra_args):
                    raise TypeError('Field may not be used twice on the same field')
                return first_arg, list(extra_args)

        return annotation, []

    @staticmethod
    def _find_field_info_arg(args: Any) -> FieldInfo | None:
        """
        Find an instance of `FieldInfo` in the provided arguments.

        Args:
            args (Any): The argument list to search for `FieldInfo`.

        Returns:
            FieldInfo | None: An instance of `FieldInfo` if found, otherwise `None`.
        """
        return next((a for a in args if isinstance(a, FieldInfo)), None)

    @classmethod
    def _collect_metadata(cls, kwargs: dict[str, Any]) -> list[Any]:
        """
        Collect annotations from kwargs.

        The return type is actually `annotated_types.BaseMetadata | PydanticMetadata`,
        but it gets combined with `list[Any]` from `Annotated[T, ...]`, hence types.

        Args:
            kwargs (dict[str, Any]): Keyword arguments passed to the function.

        Returns:
            list[Any]: A list of metadata objects - a combination of `annotated_types.BaseMetadata` and
                `PydanticMetadata`.
        """
        metadata: list[Any] = []
        general_metadata = {}
        for key, value in list(kwargs.items()):
            try:
                marker = cls.metadata_lookup[key]
            except KeyError:
                continue

            del kwargs[key]
            if value is not None:
                if marker is None:
                    general_metadata[key] = value
                else:
                    metadata.append(marker(value))
        if general_metadata:
            metadata.append(_fields.PydanticGeneralMetadata(**general_metadata))
        return metadata

    def get_default(self, *, call_default_factory: bool = False) -> Any:
        """
        Get the default value.

        We expose an option for whether to call the default_factory (if present), as calling it may
        result in side effects that we want to avoid. However, there are times when it really should
        be called (namely, when instantiating a model via `model_construct`).

        Args:
            call_default_factory (bool, optional): Whether to call the default_factory or not. Defaults to False.

        Returns:
            Any: The default value, calling the default factory if requested or `None` if not set.
        """
        if self.default_factory is None:
            return _utils.smart_deepcopy(self.default)
        elif call_default_factory:
            return self.default_factory()
        else:
            return None

    def is_required(self) -> bool:
        """Check if the argument is required.

        Returns:
            bool: `True` if the argument is required, `False` otherwise.
        """
        return self.default is Undefined and self.default_factory is None

    def rebuild_annotation(self) -> Any:
        """
        Rebuild the original annotation for use in signatures.
        """
        if not self.metadata:
            return self.annotation
        else:
            return typing_extensions._AnnotatedAlias(self.annotation, self.metadata)

    def apply_typevars_map(self, typevars_map: dict[Any, Any] | None, types_namespace: dict[str, Any] | None) -> None:
        """
        Apply a typevars_map to the annotation.

        This is used when analyzing parametrized generic types to replace typevars with their concrete types.

        See pydantic._internal._generics.replace_types for more details.
        """
        annotation = _typing_extra.eval_type_lenient(self.annotation, types_namespace, None)
        self.annotation = replace_types(annotation, typevars_map)

    def __repr_args__(self) -> ReprArgs:
        yield 'annotation', _repr.PlainRepr(_repr.display_as_type(self.annotation))
        yield 'required', self.is_required()

        for s in self.__slots__:
            if s == 'annotation':
                continue
            elif s == 'metadata' and not self.metadata:
                continue
            elif s == 'repr' and self.repr is True:
                continue
            elif s == 'final':
                continue
            if s == 'frozen' and self.frozen is False:
                continue
            if s == 'validation_alias' and self.validation_alias == self.alias:
                continue
            if s == 'serialization_alias' and self.serialization_alias == self.alias:
                continue
            if s == 'default_factory' and self.default_factory is not None:
                yield 'default_factory', _repr.PlainRepr(_repr.display_as_type(self.default_factory))
            else:
                value = getattr(self, s)
                if value is not None and value is not Undefined:
                    yield s, value


@_internal_dataclass.slots_dataclass
class AliasPath:
    path: list[int | str]

    def __init__(self, first_arg: str, *args: str | int) -> None:
        self.path = [first_arg] + list(args)

    def convert_to_aliases(self) -> list[str | int]:
        return self.path


@_internal_dataclass.slots_dataclass
class AliasChoices:
    choices: list[str | AliasPath]

    def __init__(self, *args: str | AliasPath) -> None:
        self.choices = list(args)

    def convert_to_aliases(self) -> list[list[str | int]]:
        aliases: list[list[str | int]] = []
        for c in self.choices:
            if isinstance(c, AliasPath):
                aliases.append(c.convert_to_aliases())
            else:
                aliases.append([c])
        return aliases


def Field(  # noqa C901
    default: Any = Undefined,
    *,
    default_factory: typing.Callable[[], Any] | None = None,
    alias: str | None = None,
    alias_priority: int | None = None,
    validation_alias: str | AliasPath | AliasChoices | None = None,
    serialization_alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    examples: list[Any] | None = None,
    exclude: typing.AbstractSet[int | str] | typing.Mapping[int | str, Any] | Any = None,
    include: typing.AbstractSet[int | str] | typing.Mapping[int | str, Any] | Any = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    frozen: bool = False,
    pattern: str | None = None,
    discriminator: str | None = None,
    repr: bool = True,
    strict: bool | None = None,
    json_schema_extra: dict[str, Any] | None = None,
    validate_default: bool | None = None,
    const: bool | None = None,
    unique_items: bool | None = None,
    allow_mutation: bool = True,
    regex: str | None = None,
    **extra: Any,
) -> Any:
    """
    Create a field for objects that can be configured.

    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (`int`, `float`, `Decimal`) and some apply only to `str`.

    Args:
        default (Any, optional): default value if the field is not set.
        default_factory (callable, optional): A callable to generate the default value like :func:`~datetime.utcnow`.
        alias (str, optional): an alternative name for the attribute.
        alias_priority (int, optional): priority of the alias. This defines which alias should be used in serialization.
        validation_alias (str, list of str, list of list of str, optional): 'whitelist' validation step. The field
            will be the single one allowed by the alias or set of aliases defined.
        serialization_alias (str, optional): 'blacklist' validation step. The vanilla field will be the single one of
            the alias' or set of aliases' fields and all the other fields will be ignored at serialization time.
        title (str, optional): human-readable title.
        description (str, optional): human-readable description.
        examples (list[Any], optional): An example value for this field.
        exclude (Union[AbstractSet[Union[str, int]], Mapping[Union[str, int], Any], Any]):
            Parameters that should be excluded from the field. If `None`, default
            Pydantic behaviors are used.
        include (Union[AbstractSet[Union[str, int]], Mapping[Union[str, int], Any], Any]):
            Parameters that should be included in the field. If `None`, default
            Pydantic behaviors are used.
        gt (float, optional): Greater than. If set, value must be greater than this. Only applicable to numbers.
        ge (float, optional): Greater than or equal. If set, value must be
            greater than or equal to this. Only applicable to numbers.
        lt (float, optional): Less than. If set, value must be
            less than this. Only applicable to numbers.
        le (float, optional): Less than or equal. If set, value must be
            less than or equal to this. Only applicable to numbers.
        multiple_of (float, optional): Value must be a multiple of this. Only applicable to numbers.
        allow_inf_nan (bool, optional): Allow `inf`, `-inf`, `nan`. Only applicable to numbers.
        max_digits (int, optional): Maximum number of allow digits for strings.
        decimal_places (int, optional): Maximum number decimal places allowed for numbers.
        min_items (int, optional): Minimum number of items in a collection.
        max_items (int, optional): Maximum number of items in a collection.
        min_length (int, optional): Minimum length for strings.
        max_length (int, optional): Maximum length for strings.
        frozen (bool, optional): Store the value as a frozen object if is mutable.
        pattern (str, optional): Pattern for strings.
        discriminator (str, optional): Codename for discriminating a field among others of the same type.
        repr (bool, optional): If `True` (the default), return a string representation of the field.
        strict (bool, optional): If `True` (the default is `None`), the field should be validated strictly.
        json_schema_extra (dict[str, Any]): Any other additional JSON schema data for the schema property.
        validate_default (bool, optional): Run validation that isn't only checking existence of defaults. This is
            `True` by default.
        const (bool, optional): Value is always the same literal object. This is typically a singleton object,
            such as `True` or `None`.
        unique_items (bool, optional): Require that collection items be unique.
        allow_mutation (bool, optional): If `False`, the dataclass will be frozen (made immutable).
        regex (str, optional): Regular expression pattern that the field must match against.


    Returns:
        Any: return the generated field object.
    """
    # Check deprecated & removed params of V1.
    # This has to be removed deprecation period over.
    if const:
        raise PydanticUserError('`const` is removed. use `Literal` instead', code='deprecated_kwargs')
    if min_items:
        warn('`min_items` is deprecated and will be removed. use `min_length` instead', DeprecationWarning)
        if min_length is None:
            min_length = min_items
    if max_items:
        warn('`max_items` is deprecated and will be removed. use `max_length` instead', DeprecationWarning)
        if max_length is None:
            max_length = max_items
    if unique_items is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='deprecated_kwargs',
        )
    if allow_mutation is False:
        warn('`allow_mutation` is deprecated and will be removed. use `frozen` instead', DeprecationWarning)
        frozen = True
    if regex:
        raise PydanticUserError('`regex` is removed. use `Pattern` instead', code='deprecated_kwargs')
    if extra:
        warn(
            'Extra keyword arguments on `Field` is deprecated and will be removed. use `json_schema_extra` instead',
            DeprecationWarning,
        )
        if not json_schema_extra:
            json_schema_extra = extra

    converted_validation_alias: str | list[str | int] | list[list[str | int]] | None = None
    if validation_alias:
        if not isinstance(validation_alias, (str, AliasChoices, AliasPath)):
            raise TypeError('Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`')

        if isinstance(validation_alias, (AliasChoices, AliasPath)):
            converted_validation_alias = validation_alias.convert_to_aliases()
        else:
            converted_validation_alias = validation_alias

    if serialization_alias is None and isinstance(alias, str):
        serialization_alias = alias

    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=converted_validation_alias or alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        examples=examples,
        exclude=exclude,
        include=include,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        min_items=min_items,
        max_items=max_items,
        min_length=min_length,
        max_length=max_length,
        frozen=frozen,
        pattern=pattern,
        discriminator=discriminator,
        repr=repr,
        json_schema_extra=json_schema_extra,
        strict=strict,
        validate_default=validate_default,
    )


class ModelPrivateAttr(_repr.Representation):
    """A descriptor for private attributes in class models.

    Attributes:
        default (Any): The default value of the attribute if not provided.
        default_factory (typing.Callable[[], Any]): A callable function that generates the default value of the
            attribute if not provided.
    """

    __slots__ = 'default', 'default_factory'

    def __init__(self, default: Any = Undefined, *, default_factory: typing.Callable[[], Any] | None = None) -> None:
        self.default = default
        self.default_factory = default_factory

    def __set_name__(self, cls: type[Any], name: str) -> None:
        """
        preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487
        """
        if self.default is not Undefined:
            try:
                set_name = getattr(self.default, '__set_name__')
            except AttributeError:
                pass
            else:
                if callable(set_name):
                    set_name(cls, name)

    def get_default(self) -> Any:
        """Returns the default value for the object.

        If `self.default_factory` is `None`, the method will return a deep copy of the `self.default` object.
        If `self.default_factory` is not `None`, it will call `self.default_factory` and return the value returned.

        Returns:
            Any: The default value of the object.
        """
        return _utils.smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and (self.default, self.default_factory) == (
            other.default,
            other.default_factory,
        )


def PrivateAttr(
    default: Any = Undefined,
    *,
    default_factory: typing.Callable[[], Any] | None = None,
) -> Any:
    """
    Indicates that attribute is only used internally and never mixed with regular fields.

    Private attributes are not checked by Pydantic, so it's up to you to maintain their accuracy.

    Private attributes are stored in the model `__slots__`.

    Args:
        default (Any): The attribute's default value. Defaults to Undefined.
        default_factory (typing.Callable[[], Any], optional): Callable that will be
            called when a default value is needed for this attribute.
            If both `default` and `default_factory` are set, an error will be raised.

    Returns:
        Any: An instance of `ModelPrivateAttr` class.

    Raises:
        ValueError: If both `default` and `default_factory` are set.
    """
    if default is not Undefined and default_factory is not None:
        raise TypeError('cannot specify both default and default_factory')

    return ModelPrivateAttr(
        default,
        default_factory=default_factory,
    )


@_internal_dataclass.slots_dataclass
class ComputedFieldInfo:
    """
    A container for data from `@computed_field` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: typing.ClassVar[str] = '@computed_field'
    wrapped_property: property
    json_return_type: _core_schema.JsonReturnTypes | None
    alias: str | None
    title: str | None
    description: str | None
    repr: bool


# this should really be `property[T], cached_proprety[T]` but property is not generic unlike cached_property
# See https://github.com/python/typing/issues/985 and linked issues
PropertyT = typing.TypeVar('PropertyT')


@typing.overload
def computed_field(
    *,
    json_return_type: _core_schema.JsonReturnTypes | None = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    repr: bool = True,
) -> typing.Callable[[PropertyT], PropertyT]:
    ...


@typing.overload
def computed_field(__func: PropertyT) -> PropertyT:
    ...


def computed_field(
    __f: PropertyT | None = None,
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    repr: bool = True,
    json_return_type: _core_schema.JsonReturnTypes | None = None,
) -> PropertyT | typing.Callable[[PropertyT], PropertyT]:
    """
    Decorate to include `property` and `cached_property` when serialising models.

    If applied to functions not yet decorated with `@property` or `@cached_property`, the function is
    automatically wrapped with `property`.

    Args:
        __f: the function to wrap.
        alias: alias to use when serializing this computed field, only used when `by_alias=True`
        title: Title to used when including this computed field in JSON Schema, currently unused waiting for #4697
        description: Description to used when including this computed field in JSON Schema, defaults to the functions
            docstring, currently unused waiting for #4697
        repr: whether to include this computed field in model repr
        json_return_type: optional return for serialization logic to expect when serialising to JSON, if included
            this must be correct, otherwise a `TypeError` is raised

    Returns:
        A proxy wrapper for the property.
    """

    def dec(f: Any) -> Any:
        nonlocal description
        if description is None and f.__doc__:
            description = inspect.cleandoc(f.__doc__)

        # if the function isn't already decorated with `@property` (or another descriptor), then we wrap it now
        f = _decorators.ensure_property(f)
        dec_info = ComputedFieldInfo(f, json_return_type, alias, title, description, repr)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if __f is None:
        return dec
    else:
        return dec(__f)
