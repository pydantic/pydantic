"""
Provide an enhanced dataclass that performs validation.
"""
from __future__ import annotations as _annotations

import dataclasses
import sys
import types
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, overload

from typing_extensions import Literal, dataclass_transform

from ._internal import _config, _decorators
from ._internal import _dataclasses as _pydantic_dataclasses
from ._internal._dataclasses import is_builtin_dataclass
from ._migration import getattr_migration
from .config import ConfigDict
from .fields import Field

if TYPE_CHECKING:
    from ._internal._dataclasses import PydanticDataclass

__all__ = ('dataclass',)

_T = TypeVar('_T')

if sys.version_info >= (3, 10):

    @dataclass_transform(field_specifiers=(dataclasses.field, Field))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = ...,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        """Overload for `dataclass`."""
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = ...,
    ) -> type[PydanticDataclass]:
        """Overload for `dataclass`."""
        ...

else:

    @dataclass_transform(field_specifiers=(dataclasses.field, Field))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        """Overload for `dataclass`."""
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
    ) -> type[PydanticDataclass]:
        """Overload for `dataclass`."""
        ...


@dataclass_transform(field_specifiers=(dataclasses.field, Field))
def dataclass(
    _cls: type[_T] | None = None,
    *,
    init: Literal[False] = False,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: ConfigDict | type[object] | None = None,
    validate_on_init: bool | None = None,
    kw_only: bool = False,
) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
    """
    A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclasses`,
    but with added validation.

    Args:
        _cls (type[_T] | None): The target dataclass.
        init (Literal[False]): If set to `False`, the `dataclass` will not generate an `__init__`,
            and you will need to provide one. Defaults to `False`.
        repr (bool): Determines if a `__repr__` should be generated for the class. Defaults to `True`.
        eq (bool): Determines if a `__eq__` should be generated for the class. Defaults to `True`.
        order (bool): Determines if comparison magic methods should be generated, such as `__lt__`, but
            not `__eq__`. Defaults to `False`.
        unsafe_hash (bool): Determines if an unsafe hashing function should be included in the class.
        frozen (bool): Determines if the generated class should be a 'frozen' dataclass, which does not allow its
            attributes to be modified from its constructor. Defaults to `False`.
        config (ConfigDict | type[object] | None): A configuration for the `dataclass` generation. Defaults to `None`.
        validate_on_init (bool | None): Determines whether the `dataclass` will be validated upon creation.
        kw_only (bool): Determines if keyword-only parameters should be used on the `__init__` method. Defaults
            to `False`.

    Returns:
        A callable that takes a `type` as its argument, and returns a `type` of `PydanticDataclass`. This can
        also return a `tyoe` of `PydanticDataclass` directly.

    Raises:
        AssertionError: Raised if `init` is not `False`.
    """
    assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'

    if sys.version_info >= (3, 10):
        kwargs = dict(kw_only=kw_only)
    else:
        kwargs = {}

    def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
        """Create a Pydantic dataclass from a regular dataclass.

        Args:
            cls (type[Any]): The class to create the Pydantic dataclass from.

        Returns:
            type[PydanticDataclass]: A Pydantic dataclass.

        Raises:
            TypeError: If a non-class value is provided.
        """

        original_cls = cls

        config_wrapper = _config.ConfigWrapper(config)
        decorators = _decorators.DecoratorInfos.build(cls)

        # Keep track of the original __doc__ so that we can restore it after applying the dataclasses decorator
        # Otherwise, classes with no __doc__ will have their signature added into the JSON schema description,
        # since dataclasses.dataclass will set this as the __doc__
        original_doc = cls.__doc__

        if is_builtin_dataclass(cls):
            # Don't preserve the docstring for vanilla dataclasses, as it may include the signature
            # This matches v1 behavior, and there was an explicit test for it
            original_doc = None

            # We don't want to add validation to the existing std lib dataclass, so we will subclass it
            #   If the class is generic, we need to make sure the subclass also inherits from Generic
            #   with all the same parameters.
            bases = (cls,)
            if issubclass(cls, Generic):  # type: ignore
                generic_base = Generic[cls.__parameters__]  # type: ignore
                bases = bases + (generic_base,)
            cls = types.new_class(cls.__name__, bases)

        cls = dataclasses.dataclass(  # type: ignore[call-overload]
            cls,
            init=init,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen,
            **kwargs,
        )

        cls.__pydantic_decorators__ = decorators  # type: ignore
        cls.__doc__ = original_doc
        cls.__module__ = original_cls.__module__
        cls.__qualname__ = original_cls.__qualname__
        _pydantic_dataclasses.set_dataclass_fields(cls)
        _pydantic_dataclasses.complete_dataclass(cls, config_wrapper)
        return cls

    if _cls is None:
        return create_dataclass

    return create_dataclass(_cls)


__getattr__ = getattr_migration(__name__)
