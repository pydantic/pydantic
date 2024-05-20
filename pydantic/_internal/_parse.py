from __future__ import annotations

import datetime
import re
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, Callable, Protocol, overload

import annotated_types

if TYPE_CHECKING:
    from pydantic_core import core_schema as cs

    from pydantic import GetCoreSchemaHandler


@dataclass(slots=True)
class _Parse:
    tp: type[Any]
    strict: bool = False


@dataclass(slots=True)
class _ParseDefer:
    func: Callable[[], type[Any]]

    @cached_property
    def tp(self) -> type[Any]:
        return self.func()


@dataclass(slots=True)
class _Transform:
    func: Callable[[Any], Any]


@dataclass(slots=True)
class _ValidateOr:
    left: Validate[Any, Any]
    right: Validate[Any, Any]


@dataclass
class _ValidateAnd:
    left: Validate[Any, Any]
    right: Validate[Any, Any]


_ConstraintAnnotation = (
    annotated_types.Le
    | annotated_types.Ge
    | annotated_types.Lt
    | annotated_types.Gt
    | annotated_types.Len
    | annotated_types.MultipleOf
    | annotated_types.Timezone
    | annotated_types.Interval
    | annotated_types.Predicate
    | re.Pattern[str]
)


@dataclass(slots=True)
class _Constraint:
    constraint: _ConstraintAnnotation


_Step = _Parse | _Transform | _ValidateOr | _Constraint | _ValidateAnd | _ParseDefer


@dataclass(slots=True)
class Validate[In, Out]:
    """Abstract representation of a chain of validation, transformation, and parsing steps."""

    _steps: list[_Step]

    def transform[NewOut](
        self,
        func: Callable[[Out], NewOut],
    ) -> Validate[In, NewOut]:
        return Validate[In, NewOut](self._steps + [_Transform(func)])

    @overload
    def parse[NewOut](self, tp: type[NewOut], *, strict: bool = ...) -> Validate[In, NewOut]:
        ...

    @overload
    def parse[NewOut](self: Validate[In, NewOut], *, strict: bool = ...) -> Validate[In, NewOut]:
        ...

    def parse[NewOut](self, tp: Any = ..., *, strict: bool = False) -> Validate[In, Any]:
        """Parse the input into a new type.

        If not type is provided, the type of the field is used.

        Types are parsed in Pydantic's `lax` mode by default,
        but you can enable `strict` mode by passing `strict=True`.
        """
        return Validate[In, NewOut](self._steps + [_Parse(tp, strict=strict)])

    def parse_defer[NewOut](self, func: Callable[[], type[NewOut]]) -> Validate[In, NewOut]:
        """Parse the input into a new type, deferring resolution of the type until the current class
        is fully defined.

        This is useful when you need to reference the class in it's own type annotations.
        """
        return Validate[In, NewOut](self._steps + [_ParseDefer(func)])

    # constraints
    @overload
    def constrain[NewOut: annotated_types.SupportsGe](
        self: Validate[In, NewOut], constraint: annotated_types.Ge
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut: annotated_types.SupportsGt](
        self: Validate[In, NewOut], constraint: annotated_types.Gt
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut: annotated_types.SupportsLe](
        self: Validate[In, NewOut], constraint: annotated_types.Le
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut: annotated_types.SupportsLt](
        self: Validate[In, NewOut], constraint: annotated_types.Lt
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut: _SupportsLen](
        self: Validate[In, NewOut], constraint: annotated_types.Len
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut: annotated_types.SupportsDiv](
        self: Validate[In, NewOut], constraint: annotated_types.MultipleOf
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut: datetime.datetime](
        self: Validate[In, NewOut], constraint: annotated_types.Timezone
    ) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut](self: Validate[In, NewOut], constraint: annotated_types.Predicate) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut](self: Validate[In, NewOut], constraint: annotated_types.Interval) -> Validate[In, NewOut]:
        ...

    @overload
    def constrain[NewOut](self: Validate[In, NewOut], constraint: re.Pattern[str]) -> Validate[In, NewOut]:
        ...

    def constrain(self, constraint: _ConstraintAnnotation) -> Any:
        """Constrain a value to meet a certain condition."""
        return Validate[In, Out](self._steps + [_Constraint(constraint)])

    def pattern(self: Validate[In, str], pattern: str) -> Validate[In, str]:
        """Constrain a string to match a regular expression pattern."""
        return self.constrain(re.compile(pattern))

    def gt[NewOut: annotated_types.SupportsGt](self: Validate[In, NewOut], gt: NewOut) -> Validate[In, NewOut]:
        """Constrain a value to be greater than a certain value."""
        return self.constrain(annotated_types.Gt(gt))

    def lt[NewOut: annotated_types.SupportsLt](self: Validate[In, NewOut], lt: NewOut) -> Validate[In, NewOut]:
        """Constrain a value to be less than a certain value."""
        return self.constrain(annotated_types.Lt(lt))

    def ge[NewOut: annotated_types.SupportsGe](self: Validate[In, NewOut], ge: NewOut) -> Validate[In, NewOut]:
        """Constrain a value to be greater than or equal to a certain value."""
        return self.constrain(annotated_types.Ge(ge))

    def le[NewOut: annotated_types.SupportsLe](self: Validate[In, NewOut], le: NewOut) -> Validate[In, NewOut]:
        """Constrain a value to be less than or equal to a certain value."""
        return self.constrain(annotated_types.Le(le))

    def len[NewOut: _SupportsLen](
        self: Validate[In, NewOut], min_len: int, max_len: int | None = None
    ) -> Validate[In, NewOut]:
        """Constrain a value to have a certain length."""
        return self.constrain(annotated_types.Len(min_len, max_len))

    def multiple_of[NewOut: annotated_types.SupportsDiv](
        self: Validate[In, NewOut], multiple_of: NewOut
    ) -> Validate[In, NewOut]:
        """Constrain a value to be a multiple of a certain number."""
        return self.constrain(annotated_types.MultipleOf(multiple_of))

    def predicate[NewOut](self: Validate[In, NewOut], func: Callable[[NewOut], bool]) -> Validate[In, NewOut]:
        """Constrain a value to meet a certain predicate."""
        return self.constrain(annotated_types.Predicate(func))

    # timezone methods
    def tz_naive[NewOut: datetime.datetime](
        self: Validate[In, NewOut],
    ) -> Validate[In, NewOut]:
        """Constrain a datetime to be timezone naive."""
        return self.constrain(annotated_types.Timezone(None))

    def tz_aware[NewOut: datetime.datetime](
        self: Validate[In, NewOut],
    ) -> Validate[In, NewOut]:
        """Constrain a datetime to be timezone aware."""
        return self.constrain(annotated_types.Timezone(...))

    def tz[NewOut: datetime.datetime](self: Validate[In, NewOut], tz: datetime.tzinfo) -> Validate[In, NewOut]:
        """Constrain a datetime to have a certain timezone."""
        return self.constrain(annotated_types.Timezone(tz))  # type: ignore  # TODO: what's wrong with the typing here?

    # string methods
    def lower[OutT: str](self: Validate[In, OutT]) -> Validate[In, OutT]:
        """Transform a string to lowercase."""
        return self.transform(str.lower)  # type: ignore

    def upper[OutT: str](self: Validate[In, OutT]) -> Validate[In, OutT]:
        """Transform a string to uppercase."""
        return self.transform(str.upper)  # type: ignore

    def title[OutT: str](self: Validate[In, OutT]) -> Validate[In, OutT]:
        """Transform a string to title case."""
        return self.transform(str.title)  # type: ignore

    def strip[OutT: str](self: Validate[In, OutT]) -> Validate[In, OutT]:
        """Strip whitespace from a string."""
        return self.transform(str.strip)  # type: ignore

    # operators
    def otherwise[OtherIn, OtherOut](
        self, other: Validate[OtherIn, OtherOut]
    ) -> Validate[In | OtherIn, Out | OtherOut]:
        """Combine two validation chains, returning the result of the first chain if it succeeds, and the second chain if it fails."""
        return Validate([_ValidateOr(self, other)])

    __or__ = otherwise

    def then[OtherIn, OtherOut](self, other: Validate[OtherIn, OtherOut]) -> Validate[In | OtherIn, Out | OtherOut]:
        """Pipe the result of one validation chain into another."""
        return Validate([_ValidateAnd(self, other)])

    __and__ = then

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> cs.CoreSchema:
        from pydantic_core import core_schema as cs

        queue = deque(self._steps)

        s = cs.any_schema()

        while queue:
            step = queue.popleft()
            s = _apply_step(step, s, handler, source_type)
        return s


transform = Validate[Any, Any]([]).transform
parse = Validate[Any, Any]([]).parse
parse_defer = Validate[Any, Any]([]).parse_defer
constrain = Validate[Any, Any]([]).constrain


class _SupportsLen(Protocol):
    def __len__(self) -> int:
        ...


def _check_func(func: Callable[[Any], bool], predicate_err: str | Callable[[], str]) -> Any:
    def handler(v: Any) -> Any:
        if func(v):
            return v
        raise ValueError(f'Expected {predicate_err if isinstance(predicate_err, str) else predicate_err()}')

    return handler


def _apply_step(step: _Step, s: cs.CoreSchema, handler: GetCoreSchemaHandler, source_type: Any) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    match step:
        case _Parse():
            s = _apply_parse(s, step.tp, step.strict, handler, source_type)
        case _ParseDefer():
            s = _apply_parse(s, step.tp, False, handler, source_type)
        case _Transform():
            s = _apply_transform(s, step.func)
        case _Constraint():
            s = _apply_constraint(s, step.constraint)
        case _ValidateOr():
            assert isinstance(step, _ValidateOr)
            s = cs.union_schema([handler(step.left), handler(step.right)])
        case _ValidateAnd():
            assert isinstance(step, _ValidateAnd)
            s = cs.chain_schema([handler(step.left), handler(step.right)])
    return s


def _apply_parse(
    s: cs.CoreSchema,
    tp: type[Any],
    strict: bool,
    handler: GetCoreSchemaHandler,
    source_type: Any,
) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    from pydantic import Strict

    if tp is ...:
        return handler(source_type)

    if strict:
        tp = Annotated[tp, Strict()]  # type: ignore

    if s['type'] == 'any':
        return handler(tp)
    else:
        return cs.chain_schema([s, handler(tp)])


def _apply_transform(s: cs.CoreSchema, func: Callable[[Any], Any]) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    if s['type'] == 'str':
        if func is str.strip:
            s = s.copy()
            s['strip_whitespace'] = True
            return s
        elif func is str.lower:
            s = s.copy()
            s['to_lower'] = True
            return s
        elif func is str.upper:
            s = s.copy()
            s['to_upper'] = True
            return s
    return cs.no_info_after_validator_function(func, s)


def _apply_constraint(  # noqa: C901
    s: cs.CoreSchema, constraint: _ConstraintAnnotation
) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    match constraint:
        case annotated_types.Gt(gt):
            if s['type'] in ('int', 'float', 'decimal'):
                s = s.copy()
                if s['type'] == 'int' and isinstance(gt, int):
                    s['gt'] = gt
                elif s['type'] == 'float' and isinstance(gt, float):
                    s['gt'] = gt
                elif s['type'] == 'decimal' and isinstance(gt, Decimal):
                    s['gt'] = gt
                return s

            def check_gt(v: Any) -> bool:
                return v > gt

            s = cs.no_info_after_validator_function(_check_func(check_gt, f'> {gt}'), s)
        case annotated_types.Ge(ge):

            def check_ge(v: Any) -> bool:
                return v >= ge

            s = cs.no_info_after_validator_function(_check_func(check_ge, f'>= {ge}'), s)
        case annotated_types.Lt(lt):

            def check_lt(v: Any) -> bool:
                return v < lt

            s = cs.no_info_after_validator_function(_check_func(check_lt, f'< {lt}'), s)
        case annotated_types.Le(le):

            def check_le(v: Any) -> bool:
                return v <= le

            s = cs.no_info_after_validator_function(_check_func(check_le, f'<= {le}'), s)
        case annotated_types.Len(min_len, max_len):

            def check_len(v: Any) -> bool:
                if max_len is not None:
                    return (min_len <= len(v)) and (len(v) <= max_len)
                return min_len <= len(v)

            s = cs.no_info_after_validator_function(
                _check_func(check_len, f'length >= {min_len} and length <= {max_len}'), s
            )
        case annotated_types.MultipleOf(multiple_of):

            def check_multiple_of(v: Any) -> bool:
                return v % multiple_of == 0

            s = cs.no_info_after_validator_function(_check_func(check_multiple_of, f'% {multiple_of} == 0'), s)
        case annotated_types.Timezone(tz):
            if tz is ...:

                def check_tz_aware(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    return v.tzinfo is not None

                s = cs.no_info_after_validator_function(_check_func(check_tz_aware, 'timezone aware'), s)
            elif tz is None:

                def check_tz_naive(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    return v.tzinfo is None

                s = cs.no_info_after_validator_function(_check_func(check_tz_naive, 'timezone naive'), s)
            else:
                assert isinstance(tz, datetime.tzinfo)
                offset = tz.utcoffset(None)

                def check_tz(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    assert v.tzinfo is not None
                    return v.tzinfo.utcoffset(None) == offset

                s = cs.no_info_after_validator_function(_check_func(check_tz, f'timezone {tz}'), s)
        case annotated_types.Interval(min_val, max_val):

            def check_interval(v: Any) -> bool:
                return min_val <= v <= max_val

            s = cs.no_info_after_validator_function(_check_func(check_interval, f'>= {min_val} and <= {max_val}'), s)
        case annotated_types.Predicate(func):
            if func.__name__ == '<lambda>':

                def on_lambda_err() -> str:
                    # TODO: is there a better way?
                    import inspect

                    try:
                        return (
                            '`'
                            + ''.join(
                                ''.join(inspect.getsource(func).strip().removesuffix(')').split('lambda ')[1:]).split(
                                    ':'
                                )[1:]
                            ).strip()
                            + '`'
                        )
                    except OSError:
                        # stringified annotations
                        return 'lambda'

                s = cs.no_info_after_validator_function(_check_func(func, on_lambda_err), s)
            else:
                s = cs.no_info_after_validator_function(_check_func(func, func.__name__), s)
        case re.Pattern():
            match s['type']:
                case 'str':
                    s = s.copy()
                    s['pattern'] = constraint.pattern
                case _:

                    def check_pattern(v: object) -> bool:
                        assert isinstance(v, str)
                        return constraint.match(v) is not None

                    s = cs.no_info_after_validator_function(_check_func(check_pattern, f'~ {constraint.pattern}'), s)
    return s
