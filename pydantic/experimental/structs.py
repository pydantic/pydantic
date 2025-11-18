"""Experimental `struct` type, for lightweight data structures using Pydantic validation."""

from typing import Any, Callable, Literal

from ..config import ExtraValues

# from pydantic_core._structs import create_struct_type
from ..main import BaseModel, IncEx

# TODO this is a basic skeleton implementation, to be replaced with a real one
# after the code structure is in place.


class BaseStruct(BaseModel):
    """Define a `struct` with Pydantic validation."""


def validate(
    type_: type[BaseStruct],
    data: object,
    /,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    from_attributes: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> BaseStruct:
    return type_.model_validate(
        data,
        strict=strict,
        extra=extra,
        from_attributes=from_attributes,
        context=context,
        by_alias=by_alias,
        by_name=by_name,
    )


def validate_json(
    type_: type[BaseStruct],
    data: str | bytes | bytearray,
    /,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> BaseStruct:
    return type_.model_validate_json(
        data,
        strict=strict,
        extra=extra,
        context=context,
        by_alias=by_alias,
        by_name=by_name,
    )


def validate_strings(
    type_: type[BaseStruct],
    data: Any,
    /,
    strict: bool | None = None,
    extra: ExtraValues | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> BaseStruct:
    return type_.model_validate_strings(
        data,
        strict=strict,
        extra=extra,
        context=context,
        by_alias=by_alias,
        by_name=by_name,
    )


def to_python(
    data: BaseStruct,
    /,
    mode: Literal['json', 'python'] | str = 'python',
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal['none', 'warn', 'error'] = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
) -> Any:
    return data.model_dump(
        mode=mode,
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        exclude_computed_fields=exclude_computed_fields,
        round_trip=round_trip,
        warnings=warnings,
        fallback=fallback,
        serialize_as_any=serialize_as_any,
    )


def to_json(
    data: BaseStruct,
    /,
    indent: int | None = None,
    ensure_ascii: bool = False,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal['none', 'warn', 'error'] = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
) -> Any:
    return data.model_dump_json(
        indent=indent,
        ensure_ascii=ensure_ascii,
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        exclude_computed_fields=exclude_computed_fields,
        round_trip=round_trip,
        warnings=warnings,
        fallback=fallback,
        serialize_as_any=serialize_as_any,
    )
