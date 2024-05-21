from __future__ import annotations

import datetime
import re
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, Callable, Generic, Protocol, TypeVar, overload

import annotated_types

if TYPE_CHECKING:
    from pydantic_core import core_schema as cs

    from pydantic import GetCoreSchemaHandler

from pydantic._internal._internal_dataclass import dataclass_kwargs


@dataclass(**dataclass_kwargs)
class _Parse:
    tp: type[Any]
    strict: bool = False


@dataclass(**dataclass_kwargs)
class _ParseDefer:
    func: Callable[[], type[Any]]

    @cached_property
    def tp(self) -> type[Any]:
        return self.func()


@dataclass(**dataclass_kwargs)
class _Transform:
    func: Callable[[Any], Any]


@dataclass(**dataclass_kwargs)
class _ValidateOr:
    left: Validate[Any, Any]
    right: Validate[Any, Any]


@dataclass(**dataclass_kwargs)
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


@dataclass(**dataclass_kwargs)
class _Constraint:
    constraint: _ConstraintAnnotation


_Step = _Parse | _Transform | _ValidateOr | _Constraint | _ValidateAnd | _ParseDefer


_InT = TypeVar('_InT')
_OutT = TypeVar('_OutT')
_NewOutT = TypeVar('_NewOutT')


@dataclass(**dataclass_kwargs)
class Validate(Generic[_InT, _OutT]):
    """Abstract representation of a chain of validation, transformation, and parsing steps."""

    _steps: list[_Step]

    def transform(
        self,
        func: Callable[[_OutT], _NewOutT],
    ) -> Validate[_InT, _NewOutT]:
        return Validate[_InT, _NewOutT](self._steps + [_Transform(func)])

    @overload
    def parse(self, tp: type[_NewOutT], *, strict: bool = ...) -> Validate[_InT, _NewOutT]:
        ...

    @overload
    def parse(self, *, strict: bool = ...) -> Validate[_InT, Any]:
        ...

    def parse(self, tp: Any = ..., *, strict: bool = False) -> Validate[_InT, Any]:
        """Parse the input into a new type.

        If not type is provided, the type of the field is used.

        Types are parsed in Pydantic's `lax` mode by default,
        but you can enable `strict` mode by passing `strict=True`.
        """
        return Validate[_InT, Any](self._steps + [_Parse(tp, strict=strict)])

    def parse_defer(self, func: Callable[[], type[_NewOutT]]) -> Validate[_InT, _NewOutT]:
        """Parse the input into a new type, deferring resolution of the type until the current class
        is fully defined.

        This is useful when you need to reference the class in it's own type annotations.
        """
        return Validate[_InT, _NewOutT](self._steps + [_ParseDefer(func)])

    # constraints
    @overload
    def constrain(self: Validate[_InT, _NewOutGe], constraint: annotated_types.Ge) -> Validate[_InT, _NewOutGe]:
        ...

    @overload
    def constrain(self: Validate[_InT, _NewOutGt], constraint: annotated_types.Gt) -> Validate[_InT, _NewOutGt]:
        ...

    @overload
    def constrain(self: Validate[_InT, _NewOutLe], constraint: annotated_types.Le) -> Validate[_InT, _NewOutLe]:
        ...

    @overload
    def constrain(self: Validate[_InT, _NewOutLt], constraint: annotated_types.Lt) -> Validate[_InT, _NewOutLt]:
        ...

    @overload
    def constrain(self: Validate[_InT, _NewOutLen], constraint: annotated_types.Len) -> Validate[_InT, _NewOutLen]:
        ...

    @overload
    def constrain(
        self: Validate[_InT, _NewOutDiv], constraint: annotated_types.MultipleOf
    ) -> Validate[_InT, _NewOutDiv]:
        ...

    @overload
    def constrain(
        self: Validate[_InT, _NewOutDatetime], constraint: annotated_types.Timezone
    ) -> Validate[_InT, _NewOutDatetime]:
        ...

    @overload
    def constrain(self: Validate[_InT, _OutT], constraint: annotated_types.Predicate) -> Validate[_InT, _OutT]:
        ...

    @overload
    def constrain(
        self: Validate[_InT, _NewOutInterval], constraint: annotated_types.Interval
    ) -> Validate[_InT, _NewOutInterval]:
        ...

    @overload
    def constrain(self: Validate[_InT, _NewOutT], constraint: re.Pattern[str]) -> Validate[_InT, _NewOutT]:
        ...

    def constrain(self, constraint: _ConstraintAnnotation) -> Any:
        """Constrain a value to meet a certain condition."""
        return Validate[_InT, _OutT](self._steps + [_Constraint(constraint)])

    def pattern(self: Validate[_InT, str], pattern: str) -> Validate[_InT, str]:
        """Constrain a string to match a regular expression pattern."""
        return self.constrain(re.compile(pattern))

    def gt(self: Validate[_InT, _NewOutGt], gt: _NewOutGt) -> Validate[_InT, _NewOutGt]:
        """Constrain a value to be greater than a certain value."""
        return self.constrain(annotated_types.Gt(gt))

    def lt(self: Validate[_InT, _NewOutLt], lt: _NewOutLt) -> Validate[_InT, _NewOutLt]:
        """Constrain a value to be less than a certain value."""
        return self.constrain(annotated_types.Lt(lt))

    def ge(self: Validate[_InT, _NewOutGe], ge: _NewOutGe) -> Validate[_InT, _NewOutGe]:
        """Constrain a value to be greater than or equal to a certain value."""
        return self.constrain(annotated_types.Ge(ge))

    def le(self: Validate[_InT, _NewOutLe], le: _NewOutLe) -> Validate[_InT, _NewOutLe]:
        """Constrain a value to be less than or equal to a certain value."""
        return self.constrain(annotated_types.Le(le))

    def len(self: Validate[_InT, _NewOutLen], min_len: int, max_len: int | None = None) -> Validate[_InT, _NewOutLen]:
        """Constrain a value to have a certain length."""
        return self.constrain(annotated_types.Len(min_len, max_len))

    def multiple_of(self: Validate[_InT, _NewOutDiv], multiple_of: _NewOutDiv) -> Validate[_InT, _NewOutDiv]:
        """Constrain a value to be a multiple of a certain number."""
        return self.constrain(annotated_types.MultipleOf(multiple_of))

    def predicate(self: Validate[_InT, _NewOutT], func: Callable[[_NewOutT], bool]) -> Validate[_InT, _NewOutT]:
        """Constrain a value to meet a certain predicate."""
        return self.constrain(annotated_types.Predicate(func))

    # timezone methods
    def tz_naive(
        self: Validate[_InT, _NewOutDatetime],
    ) -> Validate[_InT, _NewOutDatetime]:
        """Constrain a datetime to be timezone naive."""
        return self.constrain(annotated_types.Timezone(None))

    def tz_aware(
        self: Validate[_InT, _NewOutDatetime],
    ) -> Validate[_InT, _NewOutDatetime]:
        """Constrain a datetime to be timezone aware."""
        return self.constrain(annotated_types.Timezone(...))

    def tz(self: Validate[_InT, _NewOutDatetime], tz: datetime.tzinfo) -> Validate[_InT, _NewOutDatetime]:
        """Constrain a datetime to have a certain timezone."""
        return self.constrain(annotated_types.Timezone(tz))  # type: ignore  # TODO: what's wrong with the typing here?

    # string methods
    def lower(self: Validate[_InT, _NewOutStr]) -> Validate[_InT, str]:
        """Transform a string to lowercase."""
        return self.transform(str.lower)

    def upper(self: Validate[_InT, _NewOutStr]) -> Validate[_InT, str]:
        """Transform a string to uppercase."""
        return self.transform(str.upper)

    def title(self: Validate[_InT, _NewOutStr]) -> Validate[_InT, str]:
        """Transform a string to title case."""
        return self.transform(str.title)

    def strip(self: Validate[_InT, _NewOutStr]) -> Validate[_InT, str]:
        """Strip whitespace from a string."""
        return self.transform(str.strip)

    # operators
    def otherwise(self, other: Validate[_OtherIn, _OtherOut]) -> Validate[_InT | _OtherIn, _OutT | _OtherOut]:
        """Combine two validation chains, returning the result of the first chain if it succeeds, and the second chain if it fails."""
        return Validate([_ValidateOr(self, other)])

    __or__ = otherwise

    def then(self, other: Validate[_OtherIn, _OtherOut]) -> Validate[_InT | _OtherIn, _OutT | _OtherOut]:
        """Pipe the result of one validation chain into another."""
        return Validate([_ValidateAnd(self, other)])

    __and__ = then

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> cs.CoreSchema:
        from pydantic_core import core_schema as cs

        queue = deque(self._steps)

        s = None

        while queue:
            step = queue.popleft()
            s = _apply_step(step, s, handler, source_type)

        s = s or cs.any_schema()
        return s


parse = Validate[Any, Any]([]).parse
parse_defer = Validate[Any, Any]([]).parse_defer
transform = Validate[Any, Any]([]).transform
constrain = Validate[Any, Any]([]).constrain


def _check_func(
    func: Callable[[Any], bool], predicate_err: str | Callable[[], str], s: cs.CoreSchema | None
) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    def handler(v: Any) -> Any:
        if func(v):
            return v
        raise ValueError(f'Expected {predicate_err if isinstance(predicate_err, str) else predicate_err()}')

    if s is None:
        return cs.no_info_plain_validator_function(handler)
    else:
        return cs.no_info_after_validator_function(handler, s)


def _apply_step(step: _Step, s: cs.CoreSchema | None, handler: GetCoreSchemaHandler, source_type: Any) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    if isinstance(step, _Parse):
        s = _apply_parse(s, step.tp, step.strict, handler, source_type)
    elif isinstance(step, _ParseDefer):
        s = _apply_parse(s, step.tp, False, handler, source_type)
    elif isinstance(step, _Transform):
        s = _apply_transform(s, step.func)
    elif isinstance(step, _Constraint):
        s = _apply_constraint(s, step.constraint)
    elif isinstance(step, _ValidateOr):
        s = cs.union_schema([handler(step.left), handler(step.right)])
    else:
        assert isinstance(step, _ValidateAnd)
        s = cs.chain_schema([handler(step.left), handler(step.right)])
    return s


def _apply_parse(
    s: cs.CoreSchema | None,
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

    if s and s['type'] == 'any':
        return handler(tp)
    else:
        return cs.chain_schema([s, handler(tp)]) if s else handler(tp)


def _apply_transform(s: cs.CoreSchema | None, func: Callable[[Any], Any]) -> cs.CoreSchema:
    from pydantic_core import core_schema as cs

    if s is None:
        return cs.no_info_plain_validator_function(func)

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
    s: cs.CoreSchema | None, constraint: _ConstraintAnnotation
) -> cs.CoreSchema:
    if isinstance(constraint, annotated_types.Gt):
        gt = constraint.gt
        if s and s['type'] in ('int', 'float', 'decimal'):
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

        s = _check_func(check_gt, f'> {gt}', s)
    if isinstance(constraint, annotated_types.Ge):
        ge = constraint.ge

        def check_ge(v: Any) -> bool:
            return v >= ge

        s = _check_func(check_ge, f'>= {ge}', s)
    if isinstance(constraint, annotated_types.Lt):
        lt = constraint.lt

        def check_lt(v: Any) -> bool:
            return v < lt

        s = _check_func(check_lt, f'< {lt}', s)
    if isinstance(constraint, annotated_types.Le):
        le = constraint.le

        def check_le(v: Any) -> bool:
            return v <= le

        s = _check_func(check_le, f'<= {le}', s)
    if isinstance(constraint, annotated_types.Len):
        min_len = constraint.min_length
        max_len = constraint.max_length

        def check_len(v: Any) -> bool:
            if max_len is not None:
                return (min_len <= len(v)) and (len(v) <= max_len)
            return min_len <= len(v)

        s = _check_func(check_len, f'length >= {min_len} and length <= {max_len}', s)
    if isinstance(constraint, annotated_types.MultipleOf):
        multiple_of = constraint.multiple_of

        def check_multiple_of(v: Any) -> bool:
            return v % multiple_of == 0

        s = _check_func(check_multiple_of, f'% {multiple_of} == 0', s)
    if isinstance(constraint, annotated_types.Timezone):
        tz = constraint.tz

        if tz is ...:
            if s and s['type'] == 'datetime':
                s = s.copy()
                s['tz_constraint'] = 'aware'
            else:

                def check_tz_aware(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    return v.tzinfo is not None

                s = _check_func(check_tz_aware, 'timezone aware', s)
        elif tz is None:
            if s and s['type'] == 'datetime':
                s = s.copy()
                s['tz_constraint'] = 'naive'
            else:

                def check_tz_naive(v: object) -> bool:
                    assert isinstance(v, datetime.datetime)
                    return v.tzinfo is None

                s = _check_func(check_tz_naive, 'timezone naive', s)
        else:
            raise NotImplementedError('Constraining to a specific timezone is not yet supported')
    if isinstance(constraint, annotated_types.Interval):
        if constraint.ge:
            s = _apply_constraint(s, annotated_types.Ge(constraint.ge))
        if constraint.gt:
            s = _apply_constraint(s, annotated_types.Gt(constraint.gt))
        if constraint.le:
            s = _apply_constraint(s, annotated_types.Le(constraint.le))
        if constraint.lt:
            s = _apply_constraint(s, annotated_types.Lt(constraint.lt))
    if isinstance(constraint, annotated_types.Predicate):
        func = constraint.func

        if func.__name__ == '<lambda>':

            def on_lambda_err() -> str:
                # TODO: is there a better way?
                import inspect

                try:
                    return (
                        '`'
                        + ''.join(
                            ''.join(inspect.getsource(func).strip().removesuffix(')').split('lambda ')[1:]).split(':')[
                                1:
                            ]
                        ).strip()
                        + '`'
                    )
                except OSError:
                    # stringified annotations
                    return 'lambda'

            s = _check_func(func, on_lambda_err, s)
        else:
            s = _check_func(func, func.__name__, s)
    if isinstance(constraint, re.Pattern):
        if s and s['type'] == 'str':
            s = s.copy()
            s['pattern'] = constraint.pattern
        else:

            def check_pattern(v: object) -> bool:
                assert isinstance(v, str)
                return constraint.match(v) is not None

            s = _check_func(check_pattern, f'~ {constraint.pattern}', s)
    else:
        raise NotImplementedError(f'Constraint {constraint} is not yet supported')
    return s


class _SupportsRange(annotated_types.SupportsLe, annotated_types.SupportsGe, Protocol):
    pass


class _SupportsLen(Protocol):
    def __len__(self) -> int:
        ...


_NewOutGt = TypeVar('_NewOutGt', bound=annotated_types.SupportsGt)
_NewOutGe = TypeVar('_NewOutGe', bound=annotated_types.SupportsGe)
_NewOutLt = TypeVar('_NewOutLt', bound=annotated_types.SupportsLt)
_NewOutLe = TypeVar('_NewOutLe', bound=annotated_types.SupportsLe)
_NewOutLen = TypeVar('_NewOutLen', bound=_SupportsLen)
_NewOutDiv = TypeVar('_NewOutDiv', bound=annotated_types.SupportsDiv)
_NewOutDatetime = TypeVar('_NewOutDatetime', bound=datetime.datetime)
_NewOutInterval = TypeVar('_NewOutInterval', bound=_SupportsRange)
_NewOutStr = TypeVar('_NewOutStr', bound=str)
_OtherIn = TypeVar('_OtherIn')
_OtherOut = TypeVar('_OtherOut')
