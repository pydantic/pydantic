from __future__ import annotations as _annotations

import typing
from dataclasses import dataclass
from typing import Any

import annotated_types

from ._internal.fields import CustomMetadata, PydanticMetadata, UndefinedType
from ._internal.typing_extra import NoArgAnyCallable, display_as_type, get_args, get_origin, is_finalvar
from .utils import PyObjectStr, Representation, lenient_issubclass, smart_deepcopy

if typing.TYPE_CHECKING:
    from ._internal.typing_extra import AbstractSetIntStr, MappingIntStrAny, ReprArgs

Required: Any = Ellipsis

Undefined = UndefinedType()


@dataclass
class Strict(PydanticMetadata):
    strict: bool | None = True


@dataclass
class AllowInfNan(PydanticMetadata):
    strict: bool | None = True


class FieldInfo(Representation):
    """
    Captures extra information about a field.
    """

    __slots__ = (
        'annotation',
        'default',
        'default_factory',
        'alias',
        'alias_priority',
        'title',
        'description',
        'exclude',
        'include',
        'constraints',
        'max_digits',
        'decimal_places',
        'repr',
        'discriminator',
        'extra',
    )

    # used to convert kwargs to constraints, None has a special meaning
    __constraints_lookup__: dict[str, annotated_types.BaseMetadata | PydanticMetadata | None] = {
        'gt': annotated_types.Gt,
        'ge': annotated_types.Ge,
        'lt': annotated_types.Lt,
        'le': annotated_types.Le,
        'multiple_of': annotated_types.MultipleOf,
        'strict': Strict,
        'min_length': None,
        'max_length': None,
        'pattern': None,
        'allow_inf_nan': None,
        'min_items': None,
        'max_items': None,
        'frozen': None,
    }

    def __init__(self, **kwargs: Any) -> None:
        self.annotation, annotation_constraints = self._extract_constraints(kwargs.pop('annotation', None))

        default = kwargs.pop('default', Undefined)
        if default is Required:
            self.default = Undefined
        else:
            self.default = default

        self.default_factory = kwargs.pop('default_factory', None)

        if self.default is not Undefined and self.default_factory is not None:
            raise ValueError('cannot specify both default and default_factory')

        self.alias = kwargs.pop('alias', None)
        self.alias_priority = kwargs.pop('alias_priority', 2 if self.alias is not None else None)
        self.title = kwargs.pop('title', None)
        self.description = kwargs.pop('description', None)
        self.exclude = kwargs.pop('exclude', None)
        self.include = kwargs.pop('include', None)
        self.constraints = self._collect_constraints(kwargs) + annotation_constraints
        self.max_digits = kwargs.pop('max_digits', None)
        self.decimal_places = kwargs.pop('decimal_places', None)
        self.discriminator = kwargs.pop('discriminator', None)
        self.repr = kwargs.pop('repr', True)
        self.extra = kwargs

    @classmethod
    def from_field(cls, default: Any = Undefined, **kwargs: Any) -> 'FieldInfo':
        if 'annotation' in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        return cls(default=default, **kwargs)

    @classmethod
    def from_annotation(cls, annotation: type[Any]) -> 'FieldInfo':
        """
        Create a FieldInfo from a bare annotation - e.g. with no default value.
        """
        return cls(annotation=annotation)

    @classmethod
    def from_annotated_attribute(cls, annotation: type[Any], default: Any) -> 'FieldInfo':
        if isinstance(default, cls):
            default.annotation, annotation_constraints = cls._extract_constraints(annotation)
            default.constraints += annotation_constraints
            return default
        else:
            return cls(annotation=annotation, default=default)

    @classmethod
    def _extract_constraints(cls, annotation: type[Any] | None) -> tuple[type[Any] | None, list[Any]]:
        if annotation is not None:
            origin = get_origin(annotation)
            if lenient_issubclass(origin, typing.Annotated):
                args = get_args(annotation)
                return args[0], list(args[1:])

        return annotation, []

    @classmethod
    def _collect_constraints(cls, kwargs: dict[str, Any]) -> list[Any]:
        """
        Collect annotations from kwargs, the return type is actually `annotated_types.BaseMetadata | PydanticMetadata`
        but it gets combined with `list[Any]` from `Annotated[T, ...]`, hence types.
        """

        constraints: list[Any] = []
        generic_constraints = {}
        for key, value in list(kwargs.items()):
            try:
                marker = cls.__constraints_lookup__[key]
            except KeyError:
                continue

            del kwargs[key]
            if value is not None:
                if marker is None:
                    generic_constraints[key] = value
                else:
                    constraints.append(marker(value))
        if generic_constraints:
            constraints.append(CustomMetadata(**generic_constraints))
        return constraints

    def get_default(self) -> Any:
        return smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

    def is_required(self) -> bool:
        return self.default is Undefined and self.default_factory is None

    def __repr_args__(self) -> 'ReprArgs':
        yield 'annotation', PyObjectStr(display_as_type(self.annotation))
        yield 'required', self.is_required()

        for s in self.__slots__:
            if s == 'annotation':
                continue
            elif s == 'constraints' and not self.constraints:
                continue
            elif s == 'repr' and self.repr is True:
                continue
            if s == 'default_factory' and self.default_factory is not None:
                yield 'default_factory', PyObjectStr(display_as_type(self.default_factory))
            elif s != 'extra' or self.extra:
                value = getattr(self, s)
                if value is not None and value is not Undefined:
                    yield s, value


def Field(
    default: Any = Undefined,
    *,
    default_factory: NoArgAnyCallable | None = None,
    alias: str = None,
    title: str = None,
    description: str = None,
    exclude: AbstractSetIntStr | MappingIntStrAny | Any = None,
    include: AbstractSetIntStr | MappingIntStrAny | Any = None,
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
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (``int``, ``float``, ``Decimal``) and some apply only to ``str``.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
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
      schema will have a ``maximum`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum length. The
      schema will have a ``maxLength`` validation keyword
    :param frozen: a boolean which defaults to True. When False, the field raises a TypeError if the field is
      assigned on an instance.  The BaseModel Config must set validate_assignment to True
    :param pattern: only applies to strings, requires the field match against a regular expression
      pattern string. The schema will have a ``pattern`` validation keyword
    :param discriminator: only useful with a (discriminated a.k.a. tagged) `Union` of sub models with a common field.
      The `discriminator` is the name of this common field to shorten validation and improve generated schema
    :param repr: show this field in the representation
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
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
        **extra,
    )


class ModelPrivateAttr(Representation):
    __slots__ = 'default', 'default_factory'

    def __init__(self, default: Any = Undefined, *, default_factory: NoArgAnyCallable | None = None) -> None:
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
        return smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and (self.default, self.default_factory) == (
            other.default,
            other.default_factory,
        )


def PrivateAttr(
    default: Any = Undefined,
    *,
    default_factory: NoArgAnyCallable | None = None,
) -> Any:
    """
    Indicates that attribute is only used internally and never mixed with regular fields.

    Types or values of private attrs are not checked by pydantic, it's up to you to keep them relevant.

    Private attrs are stored in model __slots__.

    :param default: the attribute’s default value
    :param default_factory: callable that will be called when a default value is needed for this attribute
      If both `default` and `default_factory` are set, an error is raised.
    """
    if default is not Undefined and default_factory is not None:
        raise ValueError('cannot specify both default and default_factory')

    return ModelPrivateAttr(
        default,
        default_factory=default_factory,
    )


def is_finalvar_with_default_val(type_: type[Any], val: Any) -> bool:
    return is_finalvar(type_) and val is not Undefined and not isinstance(val, FieldInfo)


class DeferredType:
    """
    TODO remove
    """

    pass
