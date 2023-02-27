"""
Provide an enhanced dataclass that performs validation.
"""
from __future__ import annotations as _annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Optional, Type, TypeVar, Union, overload

from typing_extensions import Literal, dataclass_transform

from ._internal import _dataclasses as _pydantic_dataclasses
from .config import ConfigDict, get_config
from .fields import Field, FieldInfo

if TYPE_CHECKING:
    from ._internal._dataclasses import PydanticDataclass


__all__ = ('dataclass',)

_T = TypeVar('_T')

if sys.version_info >= (3, 10):

    @dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: Union[ConfigDict, Type[object], None] = None,
        validate_on_init: Optional[bool] = None,
        kw_only: bool = ...,
    ) -> Callable[[Type[_T]], PydanticDataclass]:
        ...

    @dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
    @overload
    def dataclass(
        _cls: Type[_T],
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: Union[ConfigDict, Type[object], None] = None,
        validate_on_init: Optional[bool] = None,
        kw_only: bool = ...,
    ) -> PydanticDataclass:
        ...

else:

    @dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: Union[ConfigDict, Type[object], None] = None,
        validate_on_init: Optional[bool] = None,
    ) -> Callable[[Type[_T]], PydanticDataclass]:
        ...

    @dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
    @overload
    def dataclass(
        _cls: Type[_T],
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: Union[ConfigDict, Type[object], None] = None,
        validate_on_init: Optional[bool] = None,
    ) -> PydanticDataclass:
        ...


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, FieldInfo))
def dataclass(
    _cls: Optional[Type[_T]] = None,
    *,
    init: Literal[False] = False,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Union[ConfigDict, Type[object], None] = None,
    validate_on_init: Optional[bool] = None,
    kw_only: bool = False,
) -> Union[Callable[[Type[_T]], PydanticDataclass], PydanticDataclass]:
    """
    Like the python standard lib dataclasses but enhanced with validation.
    """
    the_config = get_config(config)
    assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'

    def create_dataclass(cls: Type[Any]) -> PydanticDataclass:
        import dataclasses

        if dataclasses.is_dataclass(cls):
            # so we don't add validation to the existing dataclass
            # FIXME we need to construct `cls.__pydantic_fields__` from `cls.__dataclass_fields__` so cls
            #  "looks" like a pydantic dataclass
            cls = type(f'Sub{cls.__name__}', (cls,), {})

        _pydantic_dataclasses.prepare_dataclass(cls, the_config, kw_only)
        return dataclasses.dataclass(  # type: ignore[call-overload]
            cls,
            init=init,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen,
            kw_only=kw_only,
        )

    if _cls is None:
        return create_dataclass

    return create_dataclass(_cls)
