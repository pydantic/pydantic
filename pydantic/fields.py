from __future__ import annotations as _annotations

import typing
from copy import copy
from typing import Any

import annotated_types
import typing_extensions

from . import types
from ._internal import _fields, _forward_ref, _repr, _typing_extra, _utils
from ._internal._fields import Undefined

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
        'min_items': None,
        'max_items': None,
        'frozen': None,
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
        if _typing_extra.is_annotated(annotation):
            first_arg, *extra_args = typing_extensions.get_args(annotation)
            field_info = cls._find_field_info_arg(extra_args)
            if field_info:
                new_field_info = copy(field_info)
                new_field_info.annotation = first_arg
                new_field_info.metadata += [a for a in extra_args if not isinstance(a, FieldInfo)]
                return new_field_info

        return cls(annotation=annotation)

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

        if isinstance(default, cls):
            default.annotation, annotation_metadata = cls._extract_metadata(annotation)
            default.metadata += annotation_metadata
            return default
        elif isinstance(default, dataclasses.Field):
            pydantic_field = cls.from_dataclass_field(default)
            pydantic_field.annotation, annotation_metadata = cls._extract_metadata(annotation)
            pydantic_field.metadata += annotation_metadata
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

            return cls(annotation=annotation, default=default)

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
    alias: str = None,
    # TODO:
    #  Alternative 1: we could drop alias_priority and tell people to manually override aliases in child classes
    #  Alternative 2: we could add a new argument `override_with_alias_generator=True` equivalent to `alias_priority=1`
    alias_priority: int = None,
    title: str = None,
    description: str = None,
    examples: list[Any] = None,
    exclude: typing.AbstractSet[int | str] | typing.Mapping[int | str, Any] | Any = None,
    include: typing.AbstractSet[int | str] | typing.Mapping[int | str, Any] | Any = None,
    gt: float = None,
    ge: float = None,
    lt: float = None,
    le: float = None,
    multiple_of: float = None,
    allow_inf_nan: bool = None,
    max_digits: int = None,
    decimal_places: int = None,
    min_items: int = None,
    max_items: int = None,
    min_length: int = None,
    max_length: int = None,
    frozen: bool = None,
    pattern: str = None,
    discriminator: str = None,
    repr: bool = True,
    strict: bool | None = None,
    json_schema_extra: dict[str, Any] | None = None,
    validate_default: bool | None = None,
) -> Any:
    """
    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (``int``, ``float``, ``Decimal``) and some apply only to ``str``.

    :param default: since this is replacing the field's default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param examples: can be any list of json-encodable data, used in the schema
    :param exclude: exclude this field while dumping.
      Takes same values as the ``include`` and ``exclude`` arguments on the ``.dict`` method.
    :param include: include this field while dumping.
      Takes same values as the ``include`` and ``exclude`` arguments on the ``.dict`` method.
    :param gt: only applies to numbers, requires the field to be "greater than". The schema
      will have an ``exclusiveMinimum`` validation keyword
    :param ge: only applies to numbers, requires the field to be "greater than or equal to". The
      schema will have a ``minimum`` validation keyword
    :param lt: only applies to numbers, requires the field to be "less than". The schema
      will have an ``exclusiveMaximum`` validation keyword
    :param le: only applies to numbers, requires the field to be "less than or equal to". The
      schema will have a ``maximum`` validation keyword
    :param multiple_of: only applies to numbers, requires the field to be "a multiple of". The
      schema will have a ``multipleOf`` validation keyword
    :param allow_inf_nan: only applies to numbers, allows the field to be NaN or infinity (+inf or -inf),
        which is a valid Python float. Default True, set to False for compatibility with JSON.
    :param max_digits: only applies to Decimals, requires the field to have a maximum number
      of digits within the decimal. It does not include a zero before the decimal point or trailing decimal zeroes.
    :param decimal_places: only applies to Decimals, requires the field to have at most a number of decimal places
      allowed. It does not include trailing decimal zeroes.
    :param min_items: only applies to lists, requires the field to have a minimum number of
      elements. The schema will have a ``minItems`` validation keyword
    :param max_items: only applies to lists, requires the field to have a maximum number of
      elements. The schema will have a ``maxItems`` validation keyword
    :param min_length: only applies to strings, requires the field to have a minimum length. The
      schema will have a ``minLength`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum length. The
      schema will have a ``maxLength`` validation keyword
    :param frozen: a boolean which defaults to True. When False, the field raises a TypeError if the field is
      assigned on an instance.  The BaseModel Config must set validate_assignment to True
    :param pattern: only applies to strings, requires the field match against a regular expression
      pattern string. The schema will have a ``pattern`` validation keyword
    :param discriminator: only useful with a (discriminated a.k.a. tagged) `Union` of sub models with a common field.
      The `discriminator` is the name of this common field to shorten validation and improve generated schema
    :param repr: show this field in the representation
    :param json_schema_extra: extra dict to be merged with the JSON Schema for this field
    :param strict: enable or disable strict parsing mode
    :param validate_default: whether the default value should be validated for this field
    """
    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
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
