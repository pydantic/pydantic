"""
Provide an enhanced dataclass that performs validation.
"""
from __future__ import annotations as _annotations

import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Callable, TypeVar, overload

from typing_extensions import Literal, dataclass_transform

from ._internal import _dataclasses as _pydantic_dataclasses
from ._internal import _decorators
from .config import ConfigDict, get_config
from .fields import Field, FieldInfo

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
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field))
    @overload
    def dataclass(
        _cls: type[_T],
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
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field))
    @overload
    def dataclass(
        _cls: type[_T],
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
    Like the python standard lib dataclasses but enhanced with validation.
    """
    assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'

    def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
        # Keep track of the original __doc__ so that we can restore it after applying the dataclasses decorator
        # Otherwise, classes with no __doc__ will have their signature added into the JSON schema description,
        # since dataclasses.dataclass will set this as the __doc__
        original_doc = cls.__doc__

        decorators = _decorators.gather_decorator_functions(cls)
        if dataclasses.is_dataclass(cls) and not hasattr(cls, '__pydantic_fields__'):
            # don't preserve the docstring for vanilla dataclasses, as it may include the signature
            # this matches v1 behavior, and there was an explicit test for it
            original_doc = None

            # so we don't add validation to the existing std lib dataclass, so we subclass it, but we need to
            # set `__pydantic_fields__` while subclassing so the logic below can treat the new class like its
            # parent is a pydantic dataclass
            dc_fields = dataclasses.fields(cls)
            pydantic_fields = {}
            omitted_fields = set()
            for f in dc_fields:
                if f.init:
                    pydantic_fields[f.name] = FieldInfo.from_dataclass_field(f)
                else:
                    omitted_fields.add(f.name)
            fields = {f.name: FieldInfo.from_dataclass_field(f) for f in dataclasses.fields(cls) if f.init}
            cls = type(
                cls.__name__,
                (cls,),
                {
                    '__pydantic_fields__': fields,
                    '__pydantic_omitted_fields__': omitted_fields or None,
                    '__pydantic_decorators__': decorators,
                },
            )
        else:
            setattr(cls, '__pydantic_decorators__', decorators)

        config_dict = get_config(config, cls.__name__)
        _pydantic_dataclasses.prepare_dataclass(cls, config_dict, kw_only)

        if sys.version_info >= (3, 10):
            kwargs = dict(kw_only=kw_only)
        else:
            kwargs = {}

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
        cls.__doc__ = original_doc
        return cls

    if _cls is None:
        return create_dataclass

    return create_dataclass(_cls)
