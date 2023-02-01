"""
Logic related to validators applied to models etc. via the `@validator` and `@root_validator` decorators.
"""
from __future__ import annotations as _annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, TypeVar

from pydantic_core.core_schema import JsonReturnTypes, WhenUsed

from ..errors import PydanticUserError

if TYPE_CHECKING:
    from typing_extensions import Literal

    from ..main import BaseModel

__all__ = (
    'FIELD_VALIDATOR_TAG',
    'ROOT_VALIDATOR_TAG',
    'Validator',
    'ValidationFunctions',
    'SerializationFunctions',
    'prepare_decorator',
)
FIELD_VALIDATOR_TAG = '_field_validator'
ROOT_VALIDATOR_TAG = '_root_validator'

FIELD_SERIALIZER_TAG = '_field_serializer'


class Validator:
    """
    Store information about field and root validators.
    """

    __slots__ = 'function', 'mode', 'sub_path', 'check_fields'

    def __init__(
        self,
        *,
        mode: Literal['before', 'after', 'wrap', 'plain'],
        sub_path: tuple[str | int, ...] | None = None,
        check_fields: bool | None = None,
    ):
        # function is set later after the class is created and functions are bound
        self.function: Callable[..., Any] | None = None
        self.mode = mode
        self.sub_path = sub_path
        self.check_fields = check_fields


class Serializer:
    """
    Store information about field serializers.
    """

    __slots__ = 'function', 'sub_path', 'json_return_type', 'when_used', 'check_fields'

    def __init__(
        self,
        *,
        json_return_type: JsonReturnTypes | None = None,
        when_used: WhenUsed = 'always',
        sub_path: tuple[str | int, ...] | None = None,
        check_fields: bool | None = None,
    ):
        # arguments match core_schema.function_ser_schema
        # function is set later after the class is created and functions are bound
        self.function: Callable[..., Any] | None = None
        self.sub_path = sub_path
        self.json_return_type = json_return_type
        self.when_used = when_used
        self.check_fields = check_fields


DecFunc = TypeVar('DecFunc', Validator, Serializer)


class DecoratorFunctions(Generic[DecFunc]):
    __slots__ = (
        '_decorators',
        '_field_decorators',
        '_direct_field_decorators',
        '_all_fields_decorators',
        '_root_decorators',
        '_used_decorators',
    )
    model_attribute: ClassVar[str]
    _field_tag: ClassVar[str]
    _root_tag: ClassVar[str | None]

    def __init__(self, bases: tuple[type[Any], ...]) -> None:
        self._decorators: dict[str, DecFunc] = {}
        self._field_decorators: dict[str, list[str]] = {}
        self._direct_field_decorators: set[str] = set()
        self._all_fields_decorators: list[str] = []
        self._root_decorators: list[str] = []
        self._used_decorators: set[str] = set()
        self._inherit(bases)

    def extract_decorator(self, name: str, value: Any) -> bool:
        """
        If the value is a field or root decorator, add it to the appropriate group of decorators.

        Note at this point the function is not bound to the class,
        we have to set functions later in `set_bound_functions`.
        """
        f_decorator: tuple[tuple[str, ...], DecFunc] | None = getattr(value, self._field_tag, None)
        if f_decorator:
            fields, decorator = f_decorator
            self._decorators[name] = decorator
            for field_name in fields:
                this_field_decorators = self._field_decorators.get(field_name)
                if this_field_decorators:
                    this_field_decorators.append(name)
                else:
                    self._field_decorators[field_name] = [name]
                return True
        elif self._root_tag is not None:
            r_decorator: DecFunc | None = getattr(value, self._root_tag, None)
            if r_decorator:
                self._decorators[name] = r_decorator
                self._root_decorators.append(name)
                return True

        return False

    def set_bound_functions(self, cls: type[BaseModel]) -> None:
        """
        Set functions in self._decorators, now that the class is created and functions are bound.
        """
        for name, decorator in self._decorators.items():
            decorator.function = getattr(cls, name)

    def get_root_decorators(self) -> list[DecFunc]:
        return [self._decorators[name] for name in self._root_decorators]

    def get_field_decorators(self, name: str) -> list[DecFunc]:
        """
        Get all decorators for a given field name.
        """
        self._used_decorators.add(name)
        decorators_names = self._field_decorators.get(name, [])
        decorators_names += self._all_fields_decorators
        return [self._decorators[name] for name in decorators_names]

    def check_for_unused(self) -> None:
        unused_decorator_keys = self._decorators.keys() - self._used_decorators - set(self._root_decorators)
        unused_decorators = [name for name in unused_decorator_keys if self._decorators[name].check_fields]
        if unused_decorators:
            fn = ', '.join(unused_decorators)
            raise PydanticUserError(
                f"Decorator defined with incorrect fields: {fn} "  # noqa: Q000
                f"(use check_fields=False if you're inheriting from the model and intended this)"
            )

    def _inherit(self, bases: tuple[type[Any], ...]) -> None:
        """
        Inherit decorators from `ValidationFunctions` instances on base classes.

        Validators from the closest base should be called last, and the greatest-(grand)parent first - to roughly
        match their definition order in code.
        """
        for base in reversed(bases):
            parent_vf: DecoratorFunctions[DecFunc] | None = getattr(base, self.model_attribute, None)
            if parent_vf:
                self._decorators.update(parent_vf._decorators)
                for k, v in parent_vf._field_decorators.items():
                    existing = self._field_decorators.get(k)
                    if existing:
                        existing.extend(v)
                    self._field_decorators[k] = v[:]
                self._all_fields_decorators.extend(parent_vf._all_fields_decorators)
                self._root_decorators.extend(parent_vf._root_decorators)


class ValidationFunctions(DecoratorFunctions[Validator]):
    model_attribute: ClassVar[str] = '__pydantic_validator_functions__'
    _field_tag: ClassVar[str] = FIELD_VALIDATOR_TAG
    _root_tag: ClassVar[str | None] = ROOT_VALIDATOR_TAG


class SerializationFunctions(DecoratorFunctions[Serializer]):
    model_attribute: ClassVar[str] = '__pydantic_serializer_functions__'
    _field_tag: ClassVar[str] = FIELD_SERIALIZER_TAG
    _root_tag: ClassVar[str | None] = None


_FUNCS: set[str] = set()


def prepare_decorator(function: Callable[..., Any], allow_reuse: bool) -> classmethod[Any]:
    """
    Convert the function to a classmethod if it isn't already.

    Warn about validators/serializers with duplicated names since without this, they can be overwritten silently
    which generally isn't the intended behaviour, don't run in ipython (see #312) or if `allow_reuse` is True.
    """
    f_cls = function if isinstance(function, classmethod) else classmethod(function)
    if not allow_reuse and not in_ipython():
        ref = f'{f_cls.__func__.__module__}::{f_cls.__func__.__qualname__}'
        if ref in _FUNCS:
            warnings.warn(f'duplicate validator function "{ref}"; if this is intended, set `allow_reuse=True`')
        _FUNCS.add(ref)
    return f_cls


def in_ipython() -> bool:
    """
    Check whether we're in an ipython environment, including jupyter notebooks.
    """
    try:
        eval('__IPYTHON__')
    except NameError:
        return False
    else:  # pragma: no cover
        return True
