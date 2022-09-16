from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple, Type, TypeVar, Union

from ._internal.typing_extra import NoArgAnyCallable, is_finalvar
from .utils import Representation, ValueItems, smart_deepcopy

Required: Any = Ellipsis

T = TypeVar('T')


class UndefinedType:
    def __repr__(self) -> str:
        return 'PydanticUndefined'

    def __copy__(self: T) -> T:
        return self

    def __reduce__(self) -> str:
        return 'Undefined'

    def __deepcopy__(self: T, _: Any) -> T:
        return self


Undefined = UndefinedType()

if TYPE_CHECKING:
    from ._internal.typing_extra import AbstractSetIntStr, MappingIntStrAny, ReprArgs
    from .error_wrappers import ErrorList

    ValidateReturn = Tuple[Optional[Any], Optional[ErrorList]]
    LocStr = Union[Tuple[Union[int, str], ...], str]
    BoolUndefined = Union[bool, UndefinedType]


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
        'const',
        'gt',
        'ge',
        'lt',
        'le',
        'multiple_of',
        'allow_inf_nan',
        'max_digits',
        'decimal_places',
        'min_items',
        'max_items',
        'unique_items',
        'min_length',
        'max_length',
        'allow_mutation',
        'repr',
        'regex',
        'discriminator',
        'extra',
    )

    # field constraints with the default value, it's also used in update_from_config below
    __field_constraints__ = {
        'min_length': None,
        'max_length': None,
        'regex': None,
        'gt': None,
        'lt': None,
        'ge': None,
        'le': None,
        'multiple_of': None,
        'allow_inf_nan': None,
        'max_digits': None,
        'decimal_places': None,
        'min_items': None,
        'max_items': None,
        'unique_items': None,
        'allow_mutation': True,
    }

    def __init__(self, **kwargs: Any) -> None:
        self.annotation = kwargs.pop('annotation', None)
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
        self.const = kwargs.pop('const', None)
        self.gt = kwargs.pop('gt', None)
        self.ge = kwargs.pop('ge', None)
        self.lt = kwargs.pop('lt', None)
        self.le = kwargs.pop('le', None)
        self.multiple_of = kwargs.pop('multiple_of', None)
        self.allow_inf_nan = kwargs.pop('allow_inf_nan', None)
        self.max_digits = kwargs.pop('max_digits', None)
        self.decimal_places = kwargs.pop('decimal_places', None)
        self.min_items = kwargs.pop('min_items', None)
        self.max_items = kwargs.pop('max_items', None)
        self.unique_items = kwargs.pop('unique_items', None)
        self.min_length = kwargs.pop('min_length', None)
        self.max_length = kwargs.pop('max_length', None)
        self.allow_mutation = kwargs.pop('allow_mutation', True)
        self.regex = kwargs.pop('regex', None)
        self.discriminator = kwargs.pop('discriminator', None)
        self.repr = kwargs.pop('repr', True)
        self.extra = kwargs

    @classmethod
    def from_field(cls, default: Any = Undefined, **kwargs: Any) -> 'FieldInfo':
        if 'annotation' in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        return cls(default=default, **kwargs)

    @classmethod
    def from_annotation(cls, annotation: Any) -> 'FieldInfo':
        return cls(annotation=annotation)

    @classmethod
    def from_annotated_attribute(cls, annotation: Any, default: Any = Undefined, **kwargs: Any) -> 'FieldInfo':
        if isinstance(default, FieldInfo):
            return default
        else:
            return cls(annotation=annotation, default=default)

    def __repr_args__(self) -> 'ReprArgs':

        field_defaults_to_hide: Dict[str, Any] = {
            'repr': True,
            **self.__field_constraints__,
        }

        attrs = ((s, getattr(self, s)) for s in self.__slots__)
        return [(a, v) for a, v in attrs if v != field_defaults_to_hide.get(a, None)]

    def get_constraints(self) -> Set[str]:
        """
        Gets the constraints set on the field by comparing the constraint value with its default value

        :return: the constraints set on field_info
        """
        return {attr for attr, default in self.__field_constraints__.items() if getattr(self, attr) != default}

    def update_from_config(self, from_config: Dict[str, Any]) -> None:
        """
        Update this FieldInfo based on a dict from get_field_info, only fields which have not been set are dated.
        """
        for attr_name, value in from_config.items():
            try:
                current_value = getattr(self, attr_name)
            except AttributeError:
                # attr_name is not an attribute of FieldInfo, it should therefore be added to extra
                # (except if extra already has this value!)
                self.extra.setdefault(attr_name, value)
            else:
                if current_value is self.__field_constraints__.get(attr_name, None):
                    setattr(self, attr_name, value)
                elif attr_name == 'exclude':
                    self.exclude = ValueItems.merge(value, current_value)
                elif attr_name == 'include':
                    self.include = ValueItems.merge(value, current_value, intersect=True)

    def get_default(self) -> Any:
        return smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

    def is_required(self) -> bool:
        return self.default is Undefined and self.default_factory is None


def Field(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str = None,
    title: str = None,
    description: str = None,
    exclude: Union['AbstractSetIntStr', 'MappingIntStrAny', Any] = None,
    include: Union['AbstractSetIntStr', 'MappingIntStrAny', Any] = None,
    const: bool = None,
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
    unique_items: bool = None,
    min_length: int = None,
    max_length: int = None,
    allow_mutation: bool = True,
    regex: str = None,
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
    :param const: this field is required and *must* take it's default value
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
    :param unique_items: only applies to lists, requires the field not to have duplicated
      elements. The schema will have a ``uniqueItems`` validation keyword
    :param min_length: only applies to strings, requires the field to have a minimum length. The
      schema will have a ``maximum`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum length. The
      schema will have a ``maxLength`` validation keyword
    :param allow_mutation: a boolean which defaults to True. When False, the field raises a TypeError if the field is
      assigned on an instance.  The BaseModel Config must set validate_assignment to True
    :param regex: only applies to strings, requires the field match against a regular expression
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
        const=const,
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
        unique_items=unique_items,
        min_length=min_length,
        max_length=max_length,
        allow_mutation=allow_mutation,
        regex=regex,
        discriminator=discriminator,
        repr=repr,
        **extra,
    )


# used to be an enum but changed to int's for small performance improvement as less access overhead
SHAPE_SINGLETON = 1
SHAPE_LIST = 2
SHAPE_SET = 3
SHAPE_MAPPING = 4
SHAPE_TUPLE = 5
SHAPE_TUPLE_ELLIPSIS = 6
SHAPE_SEQUENCE = 7
SHAPE_FROZENSET = 8
SHAPE_ITERABLE = 9
SHAPE_GENERIC = 10
SHAPE_DEQUE = 11
SHAPE_DICT = 12
SHAPE_DEFAULTDICT = 13
SHAPE_COUNTER = 14
SHAPE_NAME_LOOKUP = {
    SHAPE_LIST: 'List[{}]',
    SHAPE_SET: 'Set[{}]',
    SHAPE_TUPLE_ELLIPSIS: 'Tuple[{}, ...]',
    SHAPE_SEQUENCE: 'Sequence[{}]',
    SHAPE_FROZENSET: 'FrozenSet[{}]',
    SHAPE_ITERABLE: 'Iterable[{}]',
    SHAPE_DEQUE: 'Deque[{}]',
    SHAPE_DICT: 'Dict[{}]',
    SHAPE_DEFAULTDICT: 'DefaultDict[{}]',
    SHAPE_COUNTER: 'Counter[{}]',
}

MAPPING_LIKE_SHAPES: Set[int] = {SHAPE_DEFAULTDICT, SHAPE_DICT, SHAPE_MAPPING, SHAPE_COUNTER}


class ModelField(Representation):
    pass


class ModelPrivateAttr(Representation):
    __slots__ = 'default', 'default_factory'

    def __init__(self, default: Any = Undefined, *, default_factory: Optional[NoArgAnyCallable] = None) -> None:
        self.default = default
        self.default_factory = default_factory

    def __set_name__(self, cls: Type[Any], name: str) -> None:
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
    default_factory: Optional[NoArgAnyCallable] = None,
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


class DeferredType:
    """
    Used to postpone field preparation, while creating recursive generic models.
    """


def is_finalvar_with_default_val(type_: Type[Any], val: Any) -> bool:
    return is_finalvar(type_) and val is not Undefined and not isinstance(val, FieldInfo)
