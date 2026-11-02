"""Type handlers for standard library types, such as `datetime.date`, `decimal.Decimal`, etc."""

from __future__ import annotations

import collections.abc
import datetime
import inspect
import os
import pathlib
import re
from decimal import Decimal
from fractions import Fraction
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from operator import attrgetter
from types import NoneType
from typing import Any, get_origin
from uuid import UUID
from zoneinfo import ZoneInfo

import annotated_types as at
from pydantic_core import (
    CoreSchema,
    MultiHostUrl,
    PydanticCustomError,
    PydanticSerializationUnexpectedValue,
    Url,
    core_schema,
)
from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin

from ....errors import PydanticSchemaGenerationError, PydanticUserError
from ....types import AllowInfNan, Strict
from ... import _constraints as c
from ... import _repr, _typing_extra
from .._annotations_handler import AnnotationsHandler, apply_constraints
from .._conditions import TypeIs
from .._type_handlers import GenericTypeHandler, TypeHandler
from .._type_registry import default_registry
from ._builtins import INEQUALITY, NUMERIC

# --- datetime ---


@default_registry.register
class DateTypeHandler(TypeHandler):
    """Type handler for `datetime.date`."""

    match_condition = TypeIs(datetime.date)
    known_metadata = INEQUALITY | {Strict}

    def handle_type(self, type: type[datetime.date], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'date'}, annotations_handler)


@default_registry.register
class DatetimeTypeHandler(TypeHandler):
    """Type handler for `datetime.datetime`."""

    match_condition = TypeIs(datetime.datetime)
    known_metadata = INEQUALITY | {Strict}

    def handle_type(self, type: type[datetime.datetime], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'datetime'}, annotations_handler)


@default_registry.register
class TimeTypeHandler(TypeHandler):
    """Type handler for `datetime.time`."""

    match_condition = TypeIs(datetime.time)
    known_metadata = INEQUALITY | {Strict}

    def handle_type(self, type: type[datetime.time], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'time'}, annotations_handler)


@default_registry.register
class TimedeltaTypeHandler(TypeHandler):
    """Type handler for `datetime.timedelta`."""

    match_condition = TypeIs(datetime.timedelta)
    known_metadata = NUMERIC | {Strict}

    def handle_type(self, type: type[datetime.timedelta], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'timedelta'}, annotations_handler)


# --- numbers ---


@default_registry.register
class DecimalTypeHandler(TypeHandler):
    """Type handler for `decimal.Decimal`."""

    match_condition = TypeIs(Decimal)
    known_metadata = NUMERIC | {Strict, AllowInfNan, c.MaxDigits, c.DecimalPlaces}

    def handle_type(self, type: type[Decimal], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'decimal'}, annotations_handler)


@default_registry.register
class FractionTypeHandler(TypeHandler):
    """Type handler for `fractions.Fraction`."""

    match_condition = TypeIs(Fraction)
    known_metadata = NUMERIC | {Strict}

    def handle_type(self, type: type[Fraction], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'fraction'}, annotations_handler)


# --- misc ---


@default_registry.register
class UuidTypeHandler(TypeHandler):
    """Type handler for `uuid.UUID`."""

    match_condition = TypeIs(UUID)
    known_metadata = frozenset({Strict})

    def handle_type(self, type: type[UUID], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'uuid'}, annotations_handler)


@default_registry.register
class UrlTypeHandler(TypeHandler):
    """Type handler for the `Url` and `MultiHostUrl` types of `pydantic_core`."""

    match_condition = TypeIs(Url, MultiHostUrl)
    known_metadata = frozenset({at.MaxLen, Strict})

    def handle_type(self, type: type[Url | MultiHostUrl], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema: CoreSchema = {'type': 'url'} if type is Url else {'type': 'multi-host-url'}
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class ZoneInfoTypeHandler(TypeHandler):
    """Type handler for `zoneinfo.ZoneInfo`."""

    match_condition = TypeIs(ZoneInfo)

    def handle_type(self, type: type[ZoneInfo], annotations_handler: AnnotationsHandler) -> CoreSchema:
        from ..._validators import validate_str_is_valid_iana_tz

        metadata = {'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': 'zoneinfo'}]}
        return core_schema.no_info_plain_validator_function(
            validate_str_is_valid_iana_tz,
            serialization=core_schema.to_string_ser_schema(),
            metadata=metadata,
        )


@default_registry.register
class HashableTypeHandler(TypeHandler):
    """Type handler for `collections.abc.Hashable`."""

    match_condition = TypeIs(collections.abc.Hashable)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return core_schema.custom_error_schema(
            schema=core_schema.json_or_python_schema(
                json_schema=core_schema.chain_schema(
                    [core_schema.any_schema(), core_schema.is_instance_schema(collections.abc.Hashable)]
                ),
                python_schema=core_schema.is_instance_schema(collections.abc.Hashable),
            ),
            custom_error_type='is_hashable',
            custom_error_message='Input should be hashable',
        )


@default_registry.register
class CallableTypeHandler(TypeHandler):
    """Type handler for `collections.abc.Callable` (parameterized or not)."""

    match_condition = TypeIs(collections.abc.Callable)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return {'type': 'callable'}


# --- ipaddress ---

_IP_JSON_SCHEMA_FORMATS: dict[type[Any], str] = {
    IPv4Address: 'ipv4',
    IPv4Network: 'ipv4network',
    IPv4Interface: 'ipv4interface',
    IPv6Address: 'ipv6',
    IPv6Network: 'ipv6network',
    IPv6Interface: 'ipv6interface',
}


@default_registry.register
class IpTypeHandler(TypeHandler):
    """Type handler for the `ipaddress` types."""

    match_condition = TypeIs(*_IP_JSON_SCHEMA_FORMATS)
    known_metadata = frozenset({Strict})

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        from ..._validators import IP_VALIDATOR_LOOKUP

        tp = type
        json_schema_format = _IP_JSON_SCHEMA_FORMATS[tp]

        def ser_ip(ip: Any, info: core_schema.SerializationInfo) -> Any:
            if not isinstance(ip, (tp, str)):
                raise PydanticSerializationUnexpectedValue(
                    f"Expected `{tp}` but got `{ip.__class__}` with value `'{ip}'` - serialized value may not be as expected."
                )
            if info.mode == 'python':
                return ip
            return str(ip)

        schema = core_schema.lax_or_strict_schema(
            lax_schema=core_schema.no_info_plain_validator_function(IP_VALIDATOR_LOOKUP[tp]),
            strict_schema=core_schema.json_or_python_schema(
                json_schema=core_schema.no_info_after_validator_function(tp, core_schema.str_schema()),
                python_schema=core_schema.is_instance_schema(tp),
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(ser_ip, info_arg=True, when_used='always'),
            metadata={'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': json_schema_format}]},
        )
        return apply_constraints(schema, annotations_handler)


# --- pathlib ---


@default_registry.register
class PathTypeHandler(GenericTypeHandler):
    """Type handler for the `pathlib` types and `os.PathLike`."""

    match_condition = TypeIs(
        os.PathLike,
        pathlib.Path,
        pathlib.PurePath,
        pathlib.PosixPath,
        pathlib.WindowsPath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
    )
    known_metadata = frozenset({Strict})
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        tp = type
        path_type = args[0]
        if tp is os.PathLike and (path_type not in {str, bytes} and not typing_objects.is_any(path_type)):
            raise PydanticUserError(
                '`os.PathLike` can only be used with `str`, `bytes` or `Any`', code='schema-for-unknown-type'
            )

        path_constructor = pathlib.PurePath if tp is os.PathLike else tp
        strict_inner_schema = (
            core_schema.bytes_schema(strict=True) if (path_type is bytes) else core_schema.str_schema(strict=True)
        )
        lax_inner_schema = core_schema.bytes_schema() if (path_type is bytes) else core_schema.str_schema()

        def path_validator(input_value: str | bytes) -> os.PathLike[Any]:  # type: ignore
            try:
                if path_type is bytes:
                    if isinstance(input_value, bytes):
                        try:
                            input_value = input_value.decode()
                        except UnicodeDecodeError as e:
                            raise PydanticCustomError('bytes_type', 'Input must be valid bytes') from e
                    else:
                        raise PydanticCustomError('bytes_type', 'Input must be bytes')
                elif not isinstance(input_value, str):
                    raise PydanticCustomError('path_type', 'Input is not a valid path')

                return path_constructor(input_value)  # type: ignore
            except TypeError as e:
                raise PydanticCustomError('path_type', 'Input is not a valid path') from e

        def ser_path(path: Any, info: core_schema.SerializationInfo) -> str | os.PathLike[Any]:
            if not isinstance(path, (tp, str)):
                raise PydanticSerializationUnexpectedValue(
                    f"Expected `{tp}` but got `{path.__class__}` with value `'{path}'` - serialized value may not be as expected."
                )
            if info.mode == 'python':
                return path
            return str(path)

        instance_schema = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(path_validator, lax_inner_schema),
            python_schema=core_schema.is_instance_schema(tp),
        )

        schema = core_schema.lax_or_strict_schema(
            lax_schema=core_schema.union_schema(
                [
                    instance_schema,
                    core_schema.no_info_after_validator_function(path_validator, strict_inner_schema),
                ],
                custom_error_type='path_type',
                custom_error_message=f'Input is not a valid path for {tp}',
            ),
            strict_schema=instance_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(ser_path, info_arg=True, when_used='always'),
            metadata={'pydantic_js_functions': [lambda source, handler: {**handler(source), 'format': 'path'}]},
        )
        return apply_constraints(schema, annotations_handler)


# --- re ---


@default_registry.register
class PatternTypeHandler(GenericTypeHandler):
    """Type handler for `re.Pattern` (parameterized or not)."""

    match_condition = TypeIs(re.Pattern)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        from ... import _validators

        metadata = {'pydantic_js_functions': [lambda _1, _2: {'type': 'string', 'format': 'regex'}]}
        ser = core_schema.plain_serializer_function_ser_schema(
            attrgetter('pattern'), when_used='json', return_schema=core_schema.str_schema()
        )
        if not args:
            # Unparameterized:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_either_validator, serialization=ser, metadata=metadata
            )

        param = args[0]
        if param is str:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_str_validator, serialization=ser, metadata=metadata
            )
        elif param is bytes:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_bytes_validator, serialization=ser, metadata=metadata
            )
        else:
            raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {type[param]!r}.')


# --- type ---


def _type_schema() -> CoreSchema:
    return core_schema.custom_error_schema(
        core_schema.is_instance_schema(type),
        custom_error_type='is_type',
        custom_error_message='Input should be a type',
    )


@default_registry.register
class TypeTypeHandler(GenericTypeHandler):
    """Type handler for `type` (parameterized or not)."""

    match_condition = TypeIs(type)
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._subclass_schema(args[0])

    def _union_is_subclass_schema(self, union_type: Any) -> CoreSchema:
        """Generate schema for `type[Union[X, ...]]`."""
        args = self.schema_generator._get_args_resolving_forward_refs(union_type, required=True)
        return core_schema.union_schema([self.generate_schema(type[arg]) for arg in args])

    def _subclass_schema(self, type_param: Any) -> CoreSchema:
        """Generate schema for a type, e.g. `type[int]`."""
        # Assume `type[Annotated[<typ>, ...]]` is equivalent to `type[<typ>]`:
        type_param = _typing_extra.annotated_type(type_param) or type_param

        if typing_objects.is_any(type_param):
            return _type_schema()
        elif typing_objects.is_typealiastype(type_param):
            return self.generate_schema(type[type_param.__value__])
        elif typing_objects.is_typevar(type_param):
            if type_param.__bound__:
                if is_union_origin(get_origin(type_param.__bound__)):
                    return self._union_is_subclass_schema(type_param.__bound__)
                return core_schema.is_subclass_schema(type_param.__bound__)
            elif type_param.__constraints__:
                return core_schema.union_schema([self.generate_schema(type[c]) for c in type_param.__constraints__])
            else:
                return _type_schema()
        elif is_union_origin(get_origin(type_param)):
            return self._union_is_subclass_schema(type_param)
        else:
            if typing_objects.is_self(type_param):
                type_param = self.schema_generator._resolve_self_type(type_param)
            if _typing_extra.is_generic_alias(type_param):
                raise PydanticUserError(
                    'Subscripting `type[]` with an already parametrized type is not supported. '
                    f'Instead of using type[{type_param!r}], use type[{_repr.display_as_type(get_origin(type_param))}].',
                    code=None,
                )
            if not inspect.isclass(type_param):
                # when using type[None], this doesn't type convert to type[NoneType], and None isn't a class
                # so we handle it manually here
                if type_param is None:
                    return core_schema.is_subclass_schema(NoneType)
                raise TypeError(f'Expected a class, got {type_param!r}')
            return core_schema.is_subclass_schema(type_param)
