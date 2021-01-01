import warnings
from collections import deque
from collections.abc import Iterable as CollectionsIterable
from typing import (
    TYPE_CHECKING,
    Any,
    Deque,
    Dict,
    FrozenSet,
    Generator,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from . import errors as errors_
from .class_validators import Validator, make_generic_validator, prep_validators
from .error_wrappers import ErrorWrapper
from .errors import ConfigError, NoneIsNotAllowedError
from .types import Json, JsonWrapper
from .typing import (
    NONE_TYPES,
    Callable,
    ForwardRef,
    NoArgAnyCallable,
    NoneType,
    display_as_type,
    get_args,
    get_origin,
    is_literal_type,
    is_new_type,
    new_type_supertype,
)
from .utils import PyObjectStr, Representation, lenient_issubclass, sequence_like, smart_deepcopy
from .validators import constant_validator, dict_validator, find_validators, validate_json

Required: Any = Ellipsis

T = TypeVar('T')


class UndefinedType:
    def __repr__(self) -> str:
        return 'PydanticUndefined'

    def __copy__(self: T) -> T:
        return self

    def __deepcopy__(self: T, _: Any) -> T:
        return self


Undefined = UndefinedType()

if TYPE_CHECKING:
    from .class_validators import ValidatorsList  # noqa: F401
    from .error_wrappers import ErrorList
    from .main import BaseConfig, BaseModel  # noqa: F401
    from .types import ModelOrDc  # noqa: F401
    from .typing import ReprArgs  # noqa: F401

    ValidateReturn = Tuple[Optional[Any], Optional[ErrorList]]
    LocStr = Union[Tuple[Union[int, str], ...], str]
    BoolUndefined = Union[bool, UndefinedType]


class FieldInfo(Representation):
    """
    Captures extra information about a field.
    """

    __slots__ = (
        'default',
        'default_factory',
        'alias',
        'alias_priority',
        'title',
        'description',
        'const',
        'gt',
        'ge',
        'lt',
        'le',
        'multiple_of',
        'min_items',
        'max_items',
        'min_length',
        'max_length',
        'regex',
        'extra',
    )

    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        self.default = default
        self.default_factory = kwargs.pop('default_factory', None)
        self.alias = kwargs.pop('alias', None)
        self.alias_priority = kwargs.pop('alias_priority', 2 if self.alias else None)
        self.title = kwargs.pop('title', None)
        self.description = kwargs.pop('description', None)
        self.const = kwargs.pop('const', None)
        self.gt = kwargs.pop('gt', None)
        self.ge = kwargs.pop('ge', None)
        self.lt = kwargs.pop('lt', None)
        self.le = kwargs.pop('le', None)
        self.multiple_of = kwargs.pop('multiple_of', None)
        self.min_items = kwargs.pop('min_items', None)
        self.max_items = kwargs.pop('max_items', None)
        self.min_length = kwargs.pop('min_length', None)
        self.max_length = kwargs.pop('max_length', None)
        self.regex = kwargs.pop('regex', None)
        self.extra = kwargs


def Field(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str = None,
    title: str = None,
    description: str = None,
    const: bool = None,
    gt: float = None,
    ge: float = None,
    lt: float = None,
    le: float = None,
    multiple_of: float = None,
    min_items: int = None,
    max_items: int = None,
    min_length: int = None,
    max_length: int = None,
    regex: str = None,
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
    :param min_length: only applies to strings, requires the field to have a minimum length. The
      schema will have a ``maximum`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum length. The
      schema will have a ``maxLength`` validation keyword
    :param regex: only applies to strings, requires the field match agains a regular expression
      pattern string. The schema will have a ``pattern`` validation keyword
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    if default is not Undefined and default_factory is not None:
        raise ValueError('cannot specify both default and default_factory')

    return FieldInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        const=const,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        min_items=min_items,
        max_items=max_items,
        min_length=min_length,
        max_length=max_length,
        regex=regex,
        **extra,
    )


def Schema(default: Any, **kwargs: Any) -> Any:
    warnings.warn('`Schema` is deprecated, use `Field` instead', DeprecationWarning)
    return Field(default, **kwargs)


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
SHAPE_NAME_LOOKUP = {
    SHAPE_LIST: 'List[{}]',
    SHAPE_SET: 'Set[{}]',
    SHAPE_TUPLE_ELLIPSIS: 'Tuple[{}, ...]',
    SHAPE_SEQUENCE: 'Sequence[{}]',
    SHAPE_FROZENSET: 'FrozenSet[{}]',
    SHAPE_ITERABLE: 'Iterable[{}]',
    SHAPE_DEQUE: 'Deque[{}]',
}


class ModelField(Representation):
    __slots__ = (
        'type_',
        'outer_type_',
        'sub_fields',
        'key_field',
        'validators',
        'pre_validators',
        'post_validators',
        'default',
        'default_factory',
        'required',
        'model_config',
        'name',
        'alias',
        'has_alias',
        'field_info',
        'validate_always',
        'allow_none',
        'shape',
        'class_validators',
        'parse_json',
    )

    def __init__(
        self,
        *,
        name: str,
        type_: Type[Any],
        class_validators: Optional[Dict[str, Validator]],
        model_config: Type['BaseConfig'],
        default: Any = None,
        default_factory: Optional[NoArgAnyCallable] = None,
        required: 'BoolUndefined' = Undefined,
        alias: str = None,
        field_info: Optional[FieldInfo] = None,
    ) -> None:

        self.name: str = name
        self.has_alias: bool = bool(alias)
        self.alias: str = alias or name
        self.type_: Any = type_
        self.outer_type_: Any = type_
        self.class_validators = class_validators or {}
        self.default: Any = default
        self.default_factory: Optional[NoArgAnyCallable] = default_factory
        self.required: 'BoolUndefined' = required
        self.model_config = model_config
        self.field_info: FieldInfo = field_info or FieldInfo(default)

        self.allow_none: bool = False
        self.validate_always: bool = False
        self.sub_fields: Optional[List[ModelField]] = None
        self.key_field: Optional[ModelField] = None
        self.validators: 'ValidatorsList' = []
        self.pre_validators: Optional['ValidatorsList'] = None
        self.post_validators: Optional['ValidatorsList'] = None
        self.parse_json: bool = False
        self.shape: int = SHAPE_SINGLETON
        self.model_config.prepare_field(self)
        self.prepare()

    def get_default(self) -> Any:
        return smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

    @classmethod
    def infer(
        cls,
        *,
        name: str,
        value: Any,
        annotation: Any,
        class_validators: Optional[Dict[str, Validator]],
        config: Type['BaseConfig'],
    ) -> 'ModelField':
        field_info_from_config = config.get_field_info(name)
        from .schema import get_annotation_from_field_info

        if isinstance(value, FieldInfo):
            field_info = value
            value = None if field_info.default_factory is not None else field_info.default
        else:
            field_info = FieldInfo(value, **field_info_from_config)
        required: 'BoolUndefined' = Undefined
        if value is Required:
            required = True
            value = None
        elif value is not Undefined:
            required = False
        field_info.alias = field_info.alias or field_info_from_config.get('alias')
        annotation = get_annotation_from_field_info(annotation, field_info, name)
        return cls(
            name=name,
            type_=annotation,
            alias=field_info.alias,
            class_validators=class_validators,
            default=value,
            default_factory=field_info.default_factory,
            required=required,
            model_config=config,
            field_info=field_info,
        )

    def set_config(self, config: Type['BaseConfig']) -> None:
        self.model_config = config
        info_from_config = config.get_field_info(self.name)
        config.prepare_field(self)
        new_alias = info_from_config.get('alias')
        new_alias_priority = info_from_config.get('alias_priority') or 0
        if new_alias and new_alias_priority >= (self.field_info.alias_priority or 0):
            self.field_info.alias = new_alias
            self.field_info.alias_priority = new_alias_priority
            self.alias = new_alias

    @property
    def alt_alias(self) -> bool:
        return self.name != self.alias

    def prepare(self) -> None:
        """
        Prepare the field but inspecting self.default, self.type_ etc.

        Note: this method is **not** idempotent (because _type_analysis is not idempotent),
        e.g. calling it it multiple times may modify the field and configure it incorrectly.
        """
        self._set_default_and_type()
        if self.type_.__class__ == ForwardRef:
            # self.type_ is currently a ForwardRef and there's nothing we can do now,
            # user will need to call model.update_forward_refs()
            return

        self._type_analysis()
        if self.required is Undefined:
            self.required = True
            self.field_info.default = Required
        if self.default is Undefined and self.default_factory is None:
            self.default = None
        self.populate_validators()

    def _set_default_and_type(self) -> None:
        """
        Set the default value, infer the type if needed and check if `None` value is valid.

        Note: to prevent side effects by calling the `default_factory` for nothing, we only call it
        when we want to validate the default value i.e. when `validate_all` is set to True.
        """
        if self.default_factory is not None:
            if self.type_ is Undefined:
                raise errors_.ConfigError(
                    f'you need to set the type of field {self.name!r} when using `default_factory`'
                )
            if not self.model_config.validate_all:
                return

        default_value = self.get_default()

        if default_value is not None and self.type_ is Undefined:
            self.type_ = default_value.__class__
            self.outer_type_ = self.type_

        if self.type_ is Undefined:
            raise errors_.ConfigError(f'unable to infer type for attribute "{self.name}"')

        if self.required is False and default_value is None:
            self.allow_none = True

    def _type_analysis(self) -> None:  # noqa: C901 (ignore complexity)
        # typing interface is horrible, we have to do some ugly checks
        if lenient_issubclass(self.type_, JsonWrapper):
            self.type_ = self.type_.inner_type
            self.parse_json = True
        elif lenient_issubclass(self.type_, Json):
            self.type_ = Any
            self.parse_json = True
        elif isinstance(self.type_, TypeVar):
            if self.type_.__bound__:
                self.type_ = self.type_.__bound__
            elif self.type_.__constraints__:
                self.type_ = Union[self.type_.__constraints__]
            else:
                self.type_ = Any
        elif is_new_type(self.type_):
            self.type_ = new_type_supertype(self.type_)

        if self.type_ is Any:
            if self.required is Undefined:
                self.required = False
            self.allow_none = True
            return
        elif self.type_ is Pattern:
            # python 3.7 only, Pattern is a typing object but without sub fields
            return
        elif is_literal_type(self.type_):
            return

        origin = get_origin(self.type_)
        if origin is None:
            # field is not "typing" object eg. Union, Dict, List etc.
            # allow None for virtual superclasses of NoneType, e.g. Hashable
            if isinstance(self.type_, type) and isinstance(None, self.type_):
                self.allow_none = True
            return
        if origin is Callable:
            return
        if origin is Union:
            types_ = []
            for type_ in get_args(self.type_):
                if type_ is NoneType:
                    if self.required is Undefined:
                        self.required = False
                    self.allow_none = True
                    continue
                types_.append(type_)

            if len(types_) == 1:
                # Optional[]
                self.type_ = types_[0]
                # this is the one case where the "outer type" isn't just the original type
                self.outer_type_ = self.type_
                # re-run to correctly interpret the new self.type_
                self._type_analysis()
            else:
                self.sub_fields = [self._create_sub_type(t, f'{self.name}_{display_as_type(t)}') for t in types_]
            return

        if issubclass(origin, Tuple):  # type: ignore
            # origin == Tuple without item type
            if not get_args(self.type_):
                self.type_ = Any
                self.shape = SHAPE_TUPLE_ELLIPSIS
            else:
                self.shape = SHAPE_TUPLE
                self.sub_fields = []
                for i, t in enumerate(get_args(self.type_)):
                    if t is Ellipsis:
                        self.type_ = get_args(self.type_)[0]
                        self.shape = SHAPE_TUPLE_ELLIPSIS
                        return
                    self.sub_fields.append(self._create_sub_type(t, f'{self.name}_{i}'))
            return

        if issubclass(origin, List):
            # Create self validators
            get_validators = getattr(self.type_, '__get_validators__', None)
            if get_validators:
                self.class_validators.update(
                    {f'list_{i}': Validator(validator, pre=True) for i, validator in enumerate(get_validators())}
                )

            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE_LIST
        elif issubclass(origin, Set):
            # Create self validators
            get_validators = getattr(self.type_, '__get_validators__', None)
            if get_validators:
                self.class_validators.update(
                    {f'set_{i}': Validator(validator, pre=True) for i, validator in enumerate(get_validators())}
                )

            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE_SET
        elif issubclass(origin, FrozenSet):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE_FROZENSET
        elif issubclass(origin, Deque):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE_DEQUE
        elif issubclass(origin, Sequence):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE_SEQUENCE
        elif issubclass(origin, Mapping):
            self.key_field = self._create_sub_type(get_args(self.type_)[0], 'key_' + self.name, for_keys=True)
            self.type_ = get_args(self.type_)[1]
            self.shape = SHAPE_MAPPING
        # Equality check as almost everything inherits form Iterable, including str
        # check for Iterable and CollectionsIterable, as it could receive one even when declared with the other
        elif origin in {Iterable, CollectionsIterable}:
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE_ITERABLE
            self.sub_fields = [self._create_sub_type(self.type_, f'{self.name}_type')]
        elif issubclass(origin, Type):  # type: ignore
            return
        elif hasattr(origin, '__get_validators__') or self.model_config.arbitrary_types_allowed:
            # Is a Pydantic-compatible generic that handles itself
            # or we have arbitrary_types_allowed = True
            self.shape = SHAPE_GENERIC
            self.sub_fields = [self._create_sub_type(t, f'{self.name}_{i}') for i, t in enumerate(get_args(self.type_))]
            self.type_ = origin
            return
        else:
            raise TypeError(f'Fields of type "{origin}" are not supported.')

        # type_ has been refined eg. as the type of a List and sub_fields needs to be populated
        self.sub_fields = [self._create_sub_type(self.type_, '_' + self.name)]

    def _create_sub_type(self, type_: Type[Any], name: str, *, for_keys: bool = False) -> 'ModelField':
        return self.__class__(
            type_=type_,
            name=name,
            class_validators=None if for_keys else {k: v for k, v in self.class_validators.items() if v.each_item},
            model_config=self.model_config,
        )

    def populate_validators(self) -> None:
        """
        Prepare self.pre_validators, self.validators, and self.post_validators based on self.type_'s  __get_validators__
        and class validators. This method should be idempotent, e.g. it should be safe to call multiple times
        without mis-configuring the field.
        """
        self.validate_always = getattr(self.type_, 'validate_always', False) or any(
            v.always for v in self.class_validators.values()
        )

        class_validators_ = self.class_validators.values()
        if not self.sub_fields or self.shape == SHAPE_GENERIC:
            get_validators = getattr(self.type_, '__get_validators__', None)
            v_funcs = (
                *[v.func for v in class_validators_ if v.each_item and v.pre],
                *(get_validators() if get_validators else list(find_validators(self.type_, self.model_config))),
                *[v.func for v in class_validators_ if v.each_item and not v.pre],
            )
            self.validators = prep_validators(v_funcs)

        self.pre_validators = []
        self.post_validators = []

        if self.field_info and self.field_info.const:
            self.post_validators.append(make_generic_validator(constant_validator))

        if class_validators_:
            self.pre_validators += prep_validators(v.func for v in class_validators_ if not v.each_item and v.pre)
            self.post_validators += prep_validators(v.func for v in class_validators_ if not v.each_item and not v.pre)

        if self.parse_json:
            self.pre_validators.append(make_generic_validator(validate_json))

        self.pre_validators = self.pre_validators or None
        self.post_validators = self.post_validators or None

    def validate(
        self, v: Any, values: Dict[str, Any], *, loc: 'LocStr', cls: Optional['ModelOrDc'] = None
    ) -> 'ValidateReturn':

        if self.type_.__class__ is ForwardRef:
            assert cls is not None
            raise ConfigError(
                f'field "{self.name}" not yet prepared so type is still a ForwardRef, '
                f'you might need to call {cls.__name__}.update_forward_refs().'
            )

        errors: Optional['ErrorList']
        if self.pre_validators:
            v, errors = self._apply_validators(v, values, loc, cls, self.pre_validators)
            if errors:
                return v, errors

        if v is None:
            if self.type_ in NONE_TYPES:
                # keep validating
                pass
            elif self.allow_none:
                if self.post_validators:
                    return self._apply_validators(v, values, loc, cls, self.post_validators)
                else:
                    return None, None
            else:
                return v, ErrorWrapper(NoneIsNotAllowedError(), loc)

        if self.shape == SHAPE_SINGLETON:
            v, errors = self._validate_singleton(v, values, loc, cls)
        elif self.shape == SHAPE_MAPPING:
            v, errors = self._validate_mapping(v, values, loc, cls)
        elif self.shape == SHAPE_TUPLE:
            v, errors = self._validate_tuple(v, values, loc, cls)
        elif self.shape == SHAPE_ITERABLE:
            v, errors = self._validate_iterable(v, values, loc, cls)
        elif self.shape == SHAPE_GENERIC:
            v, errors = self._apply_validators(v, values, loc, cls, self.validators)
        else:
            #  sequence, list, set, generator, tuple with ellipsis, frozen set
            v, errors = self._validate_sequence_like(v, values, loc, cls)

        if not errors and self.post_validators:
            v, errors = self._apply_validators(v, values, loc, cls, self.post_validators)
        return v, errors

    def _validate_sequence_like(  # noqa: C901 (ignore complexity)
        self, v: Any, values: Dict[str, Any], loc: 'LocStr', cls: Optional['ModelOrDc']
    ) -> 'ValidateReturn':
        """
        Validate sequence-like containers: lists, tuples, sets and generators
        Note that large if-else blocks are necessary to enable Cython
        optimization, which is why we disable the complexity check above.
        """
        if not sequence_like(v):
            e: errors_.PydanticTypeError
            if self.shape == SHAPE_LIST:
                e = errors_.ListError()
            elif self.shape in (SHAPE_TUPLE, SHAPE_TUPLE_ELLIPSIS):
                e = errors_.TupleError()
            elif self.shape == SHAPE_SET:
                e = errors_.SetError()
            elif self.shape == SHAPE_FROZENSET:
                e = errors_.FrozenSetError()
            else:
                e = errors_.SequenceError()
            return v, ErrorWrapper(e, loc)

        loc = loc if isinstance(loc, tuple) else (loc,)
        result = []
        errors: List[ErrorList] = []
        for i, v_ in enumerate(v):
            v_loc = *loc, i
            r, ee = self._validate_singleton(v_, values, v_loc, cls)
            if ee:
                errors.append(ee)
            else:
                result.append(r)

        if errors:
            return v, errors

        converted: Union[List[Any], Set[Any], FrozenSet[Any], Tuple[Any, ...], Iterator[Any], Deque[Any]] = result

        if self.shape == SHAPE_SET:
            converted = set(result)
        elif self.shape == SHAPE_FROZENSET:
            converted = frozenset(result)
        elif self.shape == SHAPE_TUPLE_ELLIPSIS:
            converted = tuple(result)
        elif self.shape == SHAPE_DEQUE:
            converted = deque(result)
        elif self.shape == SHAPE_SEQUENCE:
            if isinstance(v, tuple):
                converted = tuple(result)
            elif isinstance(v, set):
                converted = set(result)
            elif isinstance(v, Generator):
                converted = iter(result)
            elif isinstance(v, deque):
                converted = deque(result)
        return converted, None

    def _validate_iterable(
        self, v: Any, values: Dict[str, Any], loc: 'LocStr', cls: Optional['ModelOrDc']
    ) -> 'ValidateReturn':
        """
        Validate Iterables.

        This intentionally doesn't validate values to allow infinite generators.
        """

        try:
            iterable = iter(v)
        except TypeError:
            return v, ErrorWrapper(errors_.IterableError(), loc)
        return iterable, None

    def _validate_tuple(
        self, v: Any, values: Dict[str, Any], loc: 'LocStr', cls: Optional['ModelOrDc']
    ) -> 'ValidateReturn':
        e: Optional[Exception] = None
        if not sequence_like(v):
            e = errors_.TupleError()
        else:
            actual_length, expected_length = len(v), len(self.sub_fields)  # type: ignore
            if actual_length != expected_length:
                e = errors_.TupleLengthError(actual_length=actual_length, expected_length=expected_length)

        if e:
            return v, ErrorWrapper(e, loc)

        loc = loc if isinstance(loc, tuple) else (loc,)
        result = []
        errors: List[ErrorList] = []
        for i, (v_, field) in enumerate(zip(v, self.sub_fields)):  # type: ignore
            v_loc = *loc, i
            r, ee = field.validate(v_, values, loc=v_loc, cls=cls)
            if ee:
                errors.append(ee)
            else:
                result.append(r)

        if errors:
            return v, errors
        else:
            return tuple(result), None

    def _validate_mapping(
        self, v: Any, values: Dict[str, Any], loc: 'LocStr', cls: Optional['ModelOrDc']
    ) -> 'ValidateReturn':
        try:
            v_iter = dict_validator(v)
        except TypeError as exc:
            return v, ErrorWrapper(exc, loc)

        loc = loc if isinstance(loc, tuple) else (loc,)
        result, errors = {}, []
        for k, v_ in v_iter.items():
            v_loc = *loc, '__key__'
            key_result, key_errors = self.key_field.validate(k, values, loc=v_loc, cls=cls)  # type: ignore
            if key_errors:
                errors.append(key_errors)
                continue

            v_loc = *loc, k
            value_result, value_errors = self._validate_singleton(v_, values, v_loc, cls)
            if value_errors:
                errors.append(value_errors)
                continue

            result[key_result] = value_result
        if errors:
            return v, errors
        else:
            return result, None

    def _validate_singleton(
        self, v: Any, values: Dict[str, Any], loc: 'LocStr', cls: Optional['ModelOrDc']
    ) -> 'ValidateReturn':
        if self.sub_fields:
            errors = []
            for field in self.sub_fields:
                value, error = field.validate(v, values, loc=loc, cls=cls)
                if error:
                    errors.append(error)
                else:
                    return value, None
            return v, errors
        else:
            return self._apply_validators(v, values, loc, cls, self.validators)

    def _apply_validators(
        self, v: Any, values: Dict[str, Any], loc: 'LocStr', cls: Optional['ModelOrDc'], validators: 'ValidatorsList'
    ) -> 'ValidateReturn':
        for validator in validators:
            try:
                v = validator(cls, v, values, self, self.model_config)
            except (ValueError, TypeError, AssertionError) as exc:
                return v, ErrorWrapper(exc, loc)
        return v, None

    def is_complex(self) -> bool:
        """
        Whether the field is "complex" eg. env variables should be parsed as JSON.
        """
        from .main import BaseModel  # noqa: F811

        return (
            self.shape != SHAPE_SINGLETON
            or lenient_issubclass(self.type_, (BaseModel, list, set, frozenset, dict))
            or hasattr(self.type_, '__pydantic_model__')  # pydantic dataclass
        )

    def _type_display(self) -> PyObjectStr:
        t = display_as_type(self.type_)

        # have to do this since display_as_type(self.outer_type_) is different (and wrong) on python 3.6
        if self.shape == SHAPE_MAPPING:
            t = f'Mapping[{display_as_type(self.key_field.type_)}, {t}]'  # type: ignore
        elif self.shape == SHAPE_TUPLE:
            t = 'Tuple[{}]'.format(', '.join(display_as_type(f.type_) for f in self.sub_fields))  # type: ignore
        elif self.shape == SHAPE_GENERIC:
            assert self.sub_fields
            t = '{}[{}]'.format(
                display_as_type(self.type_), ', '.join(display_as_type(f.type_) for f in self.sub_fields)
            )
        elif self.shape != SHAPE_SINGLETON:
            t = SHAPE_NAME_LOOKUP[self.shape].format(t)

        if self.allow_none and (self.shape != SHAPE_SINGLETON or not self.sub_fields):
            t = f'Optional[{t}]'
        return PyObjectStr(t)

    def __repr_args__(self) -> 'ReprArgs':
        args = [('name', self.name), ('type', self._type_display()), ('required', self.required)]

        if not self.required:
            if self.default_factory is not None:
                args.append(('default_factory', f'<function {self.default_factory.__name__}>'))
            else:
                args.append(('default', self.default))

        if self.alt_alias:
            args.append(('alias', self.alias))
        return args


class ModelPrivateAttr(Representation):
    __slots__ = ('default', 'default_factory')

    def __init__(self, default: Any = Undefined, *, default_factory: Optional[NoArgAnyCallable] = None) -> None:
        self.default = default
        self.default_factory = default_factory

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

    Types or values of private attrs are not checked by pydantic and it's up to you to keep them relevant.

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
