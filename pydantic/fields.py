from __future__ import annotations as _annotations

import typing
from copy import copy
from typing import Any
from warnings import warn

import annotated_types
import typing_extensions

from . import types
from ._internal import _fields, _forward_ref, _repr, _typing_extra, _utils
from ._internal._fields import Undefined
from .errors import PydanticUserError

if typing.TYPE_CHECKING:
    from dataclasses import Field as DataclassField

    from ._internal._repr import ReprArgs


class FieldInfo(_repr.Representation):
    """
    Hold information about a field, FieldInfo is used however a field is defined, whether or not the `Field()`
    function below is explicitly used.
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
            raise ValueError('cannot specify both default and default_factory')

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
        # currently only used on dataclasses
        self.init_var = kwargs.get('init_var', None)
        self.kw_only = kwargs.get('kw_only', None)
        self.validate_default = kwargs.get('validate_default', None)
        self.frozen = kwargs.get('frozen', None)
        self.final = kwargs.get('final', None)

    @classmethod
    def from_field(cls, default: Any = Undefined, **kwargs: Any) -> FieldInfo:
        """
        Create `FieldInfo` with the `Field` function, e.g.:
        >>> import pydantic
        >>> class MyModel(pydantic.BaseModel):
        >>>     foo: int = pydantic.Field(4, ...)  # <-- like this
        """
        # TODO: This is a good place to add migration warnings; should we use overload for type-hinting the signature?
        if 'annotation' in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        return cls(default=default, **kwargs)

    @classmethod
    def from_annotation(cls, annotation: type[Any] | _forward_ref.PydanticForwardRef) -> FieldInfo:
        """
        Create `FieldInfo` from a bare annotation, e.g.:
        >>> import pydantic
        >>> class MyModel(pydantic.BaseModel):
        >>>     foo: int  # <-- like this

        We also account for the case where the annotation can be an instance of `Annotated` and where
        one of the (not first) arguments in `Annotated` are an instance of `FieldInfo`, e.g.:
        >>> import pydantic, annotated_types, typing
        >>> class MyModel(pydantic.BaseModel):
        >>>     foo: typing.Annotated[int, annotated_types.Gt(42)]
        >>>     bar: typing.Annotated[int, Field(gt=42)]
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
        Create `FieldInfo` from an annotation with a default value, e.g.:
        >>> import pydantic, annotated_types, typing
        >>> class MyModel(pydantic.BaseModel):
        >>>     foo: int = 4  # <-- like this
        >>>     bar: typing.Annotated[int, annotated_types.Gt(4)] = 4  # <-- or this
        >>>     spam: typing.Annotated[int, pydantic.Field(gt=4)] = 4  # <-- or this
        """
        import dataclasses

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
            pydantic_field = cls.from_dataclass_field(default)
            pydantic_field.annotation, annotation_metadata = cls._extract_metadata(annotation)
            pydantic_field.metadata += annotation_metadata
            pydantic_field.final = final
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
    def from_dataclass_field(cls, dc_field: DataclassField[Any]) -> FieldInfo:
        """
        Construct a `FieldInfo` from a `dataclasses.Field` instance.
        """
        import dataclasses

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
        """
        Try to extract metadata/constraints from an annotation if it's using `Annotated`.

        Returns a tuple of `(annotation_type, annotation_metadata)`.
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
        Find an instance of `FieldInfo` if it's in args, expected to be called with all but the first argument of
        `Annotated`.
        """
        return next((a for a in args if isinstance(a, FieldInfo)), None)

    @classmethod
    def _collect_metadata(cls, kwargs: dict[str, Any]) -> list[Any]:
        """
        Collect annotations from kwargs, the return type is actually `annotated_types.BaseMetadata | PydanticMetadata`
        but it gets combined with `list[Any]` from `Annotated[T, ...]`, hence types.
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
        We expose an option for whether to call the default_factory (if present), as calling it may
        result in side effects that we want to avoid. However, there are times when it really should
        be called (namely, when instantiating a model via `model_construct`).
        """
        if self.default_factory is None:
            return _utils.smart_deepcopy(self.default)
        elif call_default_factory:
            return self.default_factory()
        else:
            return None

    def is_required(self) -> bool:
        return self.default is Undefined and self.default_factory is None

    def rebuild_annotation(self) -> Any:
        """
        Rebuild the original annotation for use in signatures.
        """
        if not self.metadata:
            return self.annotation
        else:
            return typing_extensions._AnnotatedAlias(self.annotation, self.metadata)

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


def Field(
    default: Any = Undefined,
    *,
    default_factory: typing.Callable[[], Any] | None = None,
    alias: str | None = None,
    alias_priority: int | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
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
    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (`int`, `float`, `Decimal`) and some apply only to `str`.

    Args:
        default (Any): The default value is returned if the corresponding field value is not present in the input data
            or if the data value is None. Defaults to `Undefined`.
        default_factory (typing.Callable[[], Any] | None): A callable that returns the default value for the field.
            Only used if default is not set. Defaults to `None`.
        alias (str | None): The alias for the field. Defaults to `None`.
        alias_priority (int | None): The priority score for the field if it is an alias for another field. Defaults to
            `None`.
        validation_alias (str | list[str | int] | list[list[str | int]] | None): The alias(es) to use to find the field
            value during validation. Defaults to `None`. TODO: Add documentation reference for non-str alias variants
        serialization_alias (str | None): The alias to use as a key when serializing. Defaults to `None`.
        title (str | None): The title for the field. Defaults to `None`.
        description (str | None): The description for the field. Defaults to `None`.
        examples (list[Any] | None): Examples of the field values. Defaults to `None`.
        exclude (typing.AbstractSet[int | str] | typing.Mapping[int | str, Any] | Any): A set or mapping of keys that
            should be excluded from the input data. Defaults to `None`.
        include (typing.AbstractSet[int | str] | typing.Mapping[int | str, Any] | Any): A set or mapping of keys that
            should be included in the input data. Defaults to `None`.
        gt (float | None): The minimum value of the field. Defaults to `None`.
        ge (float | None): The minimum value of the field (inclusive). Defaults to `None`.
        lt (float | None): The maximum value of the field. Defaults to `None`.
        le (float | None): The maximum value of the field (inclusive). Defaults to `None`.
        multiple_of (float | None): The field value must be a multiple of this value. Defaults to `None`.
        allow_inf_nan (bool | None): Determines whether the field can be populated with infinity or NaN values.
            Defaults to `None`.
        max_digits (int | None): The maximum number of digits in a decimal number. Defaults to `None`.
        decimal_places (int | None): The maximum number of decimal places allowed in a decimal number.
            Defaults to `None`.
        min_items (int | None): The minimum number of items allowed in a sequence. Defaults to `None`.
        max_items (int | None): The maximum number of items allowed in a sequence. Defaults to `None`.
        min_length (int | None): The minimum length of a string field. Defaults to `None`.
        max_length (int | None): The maximum length of a string field. Defaults to `None`.
        frozen (bool | None): Determines whether the value is immutable. Defaults to `None`.
        pattern (str | None): A regular expression pattern used to validate string fields. Defaults to `None`.
        discriminator (str | None): The discriminator value for a polymorphic model. Defaults to `None`.
        repr (bool): Determines whether the field value should be included in the object's string representation.
            Defaults to True.
        strict (bool | None): Used to determine whether the object should be marked as invalid if an unknown field is
            detected. Defaults to `None`.
        json_schema_extra (dict[str, Any] | None): A dictionary containing any additional metadata about the field.
            Defaults to `None`.
        validate_default (bool | None): Determines whether the default value for the field should be validated.
            Defaults to `None`.

    Returns:
        Any: The field for the attribute.
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
    if unique_items:
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

    if validation_alias is None:
        validation_alias = alias
    if serialization_alias is None and isinstance(alias, str):
        serialization_alias = alias

    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
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

    Types or values of private attrs are not checked by pydantic, it's up to you to keep them relevant.

    Private attrs are stored in model __slots__.

    :param default: the attribute's default value
    :param default_factory: callable that will be called when a default value is needed for this attribute
      If both `default` and `default_factory` are set, an error is raised.
    """
    if default is not Undefined and default_factory is not None:
        raise ValueError('cannot specify both default and default_factory')

    return ModelPrivateAttr(
        default,
        default_factory=default_factory,
    )
