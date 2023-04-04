from __future__ import annotations as _annotations

import typing
from copy import deepcopy
from enum import Enum
from typing import Any

from .._internal import (
    _model_construction,
    _typing_extra,
    _utils,
)
from .._internal._fields import Undefined

if typing.TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic._internal._utils import AbstractSetIntStr, MappingIntStrAny

    AnyClassMethod = classmethod[Any]
    TupleGenerator = typing.Generator[tuple[str, Any], None, None]
    Model = typing.TypeVar('Model', bound='BaseModel')
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx = set[int] | set[str] | dict[int, Any] | dict[str, Any] | None

_object_setattr = _model_construction.object_setattr


def _iter(
    self: BaseModel,
    to_dict: bool = False,
    by_alias: bool = False,
    include: AbstractSetIntStr | MappingIntStrAny | None = None,
    exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> TupleGenerator:
    # Merge field set excludes with explicit exclude parameter with explicit overriding field set options.
    # The extra "is not None" guards are not logically necessary but optimizes performance for the simple case.
    if exclude is not None:
        exclude = _utils.ValueItems.merge(
            {k: v.exclude for k, v in self.model_fields.items() if v.exclude is not None}, exclude
        )

    if include is not None:
        include = _utils.ValueItems.merge({k: v.include for k, v in self.model_fields.items()}, include, intersect=True)

    allowed_keys = _calculate_keys(self, include=include, exclude=exclude, exclude_unset=exclude_unset)  # type: ignore
    if allowed_keys is None and not (to_dict or by_alias or exclude_unset or exclude_defaults or exclude_none):
        # huge boost for plain _iter()
        yield from self.__dict__.items()
        return

    value_exclude = _utils.ValueItems(self, exclude) if exclude is not None else None
    value_include = _utils.ValueItems(self, include) if include is not None else None

    for field_key, v in self.__dict__.items():
        if (allowed_keys is not None and field_key not in allowed_keys) or (exclude_none and v is None):
            continue

        if exclude_defaults:
            try:
                field = self.model_fields[field_key]
            except KeyError:
                pass
            else:
                if not field.is_required() and field.default == v:
                    continue

        if by_alias and field_key in self.model_fields:
            dict_key = self.model_fields[field_key].alias or field_key
        else:
            dict_key = field_key

        if to_dict or value_include or value_exclude:
            v = _get_value(  # type: ignore[no-untyped-call]
                type(self),
                v,
                to_dict=to_dict,
                by_alias=by_alias,
                include=value_include and value_include.for_element(field_key),
                exclude=value_exclude and value_exclude.for_element(field_key),
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        yield dict_key, v


def _copy_and_set_values(
    self: Model, values: typing.Dict[str, Any], fields_set: set[str], *, deep: bool  # noqa UP006
) -> Model:
    if deep:
        # chances of having empty dict here are quite low for using smart_deepcopy
        values = deepcopy(values)

    cls = self.__class__
    m = cls.__new__(cls)
    _object_setattr(m, '__dict__', values)
    _object_setattr(m, '__fields_set__', fields_set)
    for name in self.__private_attributes__:
        value = getattr(self, name, Undefined)
        if value is not Undefined:
            if deep:
                value = deepcopy(value)
            _object_setattr(m, name, value)

    return m


@typing.no_type_check
def _get_value(
    cls: type[BaseModel],
    v: Any,
    to_dict: bool,
    by_alias: bool,
    include: AbstractSetIntStr | MappingIntStrAny | None,
    exclude: AbstractSetIntStr | MappingIntStrAny | None,
    exclude_unset: bool,
    exclude_defaults: bool,
    exclude_none: bool,
) -> Any:
    from pydantic import BaseModel

    if isinstance(v, BaseModel):
        if to_dict:
            return v.model_dump(
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                include=include,
                exclude=exclude,
                exclude_none=exclude_none,
            )
        else:
            return v.copy(include=include, exclude=exclude)

    value_exclude = _utils.ValueItems(v, exclude) if exclude else None
    value_include = _utils.ValueItems(v, include) if include else None

    if isinstance(v, dict):
        return {
            k_: _get_value(
                cls,
                v_,
                to_dict=to_dict,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                include=value_include and value_include.for_element(k_),
                exclude=value_exclude and value_exclude.for_element(k_),
                exclude_none=exclude_none,
            )
            for k_, v_ in v.items()
            if (not value_exclude or not value_exclude.is_excluded(k_))
            and (not value_include or value_include.is_included(k_))
        }

    elif _utils.sequence_like(v):
        seq_args = (
            _get_value(
                cls,
                v_,
                to_dict=to_dict,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                include=value_include and value_include.for_element(i),
                exclude=value_exclude and value_exclude.for_element(i),
                exclude_none=exclude_none,
            )
            for i, v_ in enumerate(v)
            if (not value_exclude or not value_exclude.is_excluded(i))
            and (not value_include or value_include.is_included(i))
        )

        return v.__class__(*seq_args) if _typing_extra.is_namedtuple(v.__class__) else v.__class__(seq_args)

    elif isinstance(v, Enum) and getattr(cls.model_config, 'use_enum_values', False):
        return v.value

    else:
        return v


def _calculate_keys(
    self: BaseModel,
    include: MappingIntStrAny | None,
    exclude: MappingIntStrAny | None,
    exclude_unset: bool,
    update: typing.Dict[str, Any] | None = None,  # noqa UP006
) -> typing.AbstractSet[str] | None:
    if include is None and exclude is None and exclude_unset is False:
        return None

    keys: typing.AbstractSet[str]
    if exclude_unset:
        keys = self.__fields_set__.copy()
    else:
        keys = self.__dict__.keys()

    if include is not None:
        keys &= include.keys()

    if update:
        keys -= update.keys()

    if exclude:
        keys -= {k for k, v in exclude.items() if _utils.ValueItems.is_true(v)}

    return keys
