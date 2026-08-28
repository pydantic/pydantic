"""Single-pass evaluation and inspection of annotations.

The `AnnotationEvaluator` class is a `TypeHintTransformer` walking over an annotation expression once, and:

- evaluating the forward references it contains (what `typing._eval_type()` does), *owning* the whole
  evaluation chain on Python 3.14+ (where `ForwardRef.evaluate()` doesn't recurse into the evaluated value).
- keeping track of the type qualifiers and `Annotated` metadata surrounding the type expression
  (what `typing_inspection.introspection.inspect_annotation()` does).
- computing a cache key for *pure* type expressions (see `_PURE_LEAF_TYPES`) as it goes, so that the core
  schema for such types can be cached process-wide.
"""

from __future__ import annotations as _annotations

import datetime
import sys
import typing
from dataclasses import InitVar
from decimal import Decimal
from types import NoneType
from typing import Annotated, Any, ForwardRef, NamedTuple, cast

import typing_extensions
from typing_inspection import typing_objects
from typing_inspection.introspection import (
    UNKNOWN,
    AnnotationSource,
    ForbiddenQualifier,
    Qualifier,
    inspect_annotation,
    is_union_origin,
)
from typing_inspection.introspection._parsing import InvalidExpression, TypeHintTransformer

from ._namespace_utils import GlobalsNamespace, MappingNamespace
from ._typing_extra import eval_type, raise_eval_type_error

if sys.version_info < (3, 14):
    from ._typing_extra import _eval_type as _stdlib_eval_type

__all__ = ('NOT_PURE', 'AnnotationEvaluator', 'EvaluatedAnnotation')

_TypingGenericAlias: type[Any] = type(typing.List[int])  # noqa: UP006
"""The private `typing._GenericAlias` class (*exact* instances of it are the `typing.List[int]`, `ClassVar[int]`, ... forms).

For such instances (and for `types.GenericAlias` instances), the `__origin__` attribute is what `get_origin()` returns.
"""

_UNION_ORIGIN: Any = typing_extensions.get_origin(int | str)

_INSPECTED_QUALIFIER_ORIGINS: dict[int, Qualifier] = {
    # (`typing_extensions` re-exports the `typing` objects when available)
    id(typing_extensions.ClassVar): 'class_var',
    id(typing_extensions.Final): 'final',
    id(typing_extensions.Required): 'required',
    id(typing_extensions.NotRequired): 'not_required',
    id(typing_extensions.ReadOnly): 'read_only',
}
"""The origins of parameterized type qualifiers (`ClassVar[int]`, `Final[int]`, ...) by identity."""

# Pure annotations: annotations exclusively made of the following leaf types and unions, `Literal` forms
# of primitive values and builtin containers of those. The core schema generated for a pure annotation
# (without any metadata attached) only ever depends on the annotation itself: the leaf types are immutable
# builtin types (or typing special forms) which can't have `__get_pydantic_core_schema__()` (or alike)
# hooks defined, no configuration value is involved (at the exception of the deprecated `json_encoders`,
# which is checked for separately) and no schema generation context (namespaces -- no forward
# annotations can be present --, definitions, type variables map) is involved.
# Note: membership is checked by identity, so that no user-defined type with a custom
# `__eq__()`/`__hash__()` can be considered pure (the objects are kept alive by the tuple).
_PURE_LEAF_TYPES: tuple[Any, ...] = (
    str,
    bytes,
    int,
    float,
    bool,
    complex,
    object,
    None,
    NoneType,
    Any,
    typing_extensions.Any,
    datetime.date,
    datetime.datetime,
    datetime.time,
    datetime.timedelta,
    Decimal,
    list,
    set,
    frozenset,
    dict,
    tuple,
    # For `tuple[<type>, ...]` forms:
    Ellipsis,
)
_PURE_LEAF_TYPE_IDS: dict[int, Any] = {id(tp): tp for tp in _PURE_LEAF_TYPES}
_PURE_CONTAINER_ORIGINS: tuple[Any, ...] = (list, set, frozenset, dict, tuple)
_PURE_CONTAINER_ORIGIN_IDS: dict[int, Any] = {id(tp): tp for tp in _PURE_CONTAINER_ORIGINS}
_PURE_LITERAL_VALUE_TYPE_IDS: dict[int, Any] = {id(tp): tp for tp in (str, bytes, int, bool, NoneType)}

NOT_PURE: Any = object()
"""Sentinel value used as the `pure_key` of `EvaluatedAnnotation` for non pure annotations."""


class EvaluatedAnnotation(NamedTuple):
    """The result of `AnnotationEvaluator.evaluate()`."""

    annotation: Any
    """The full annotation, with forward references evaluated (or the original annotation if `evaluated` is `False`).

    This is what `typing._eval_type()` would return for the annotation.
    """

    type: Any
    """The type expression, with type qualifiers and `Annotated` forms stripped (or `UNKNOWN` for bare qualifiers)."""

    qualifiers: set[Qualifier]
    """The type qualifiers found on the annotation."""

    metadata: list[Any]
    """The `Annotated` metadata found on the annotation."""

    evaluated: bool
    """Whether the annotation was successfully evaluated (i.e. no `NameError` was raised)."""

    pure_key: Any
    """A hashable cache key if the type expression is *pure* and no metadata is attached, `NOT_PURE` otherwise.

    The type expression can't be used directly as a key, as unions and `Literal` forms compare equal
    irrespective of the order of their members, but core schemas depend on the order. Keys are the leaf
    type for leaf types, or else nested tuples mirroring the type expression.
    """


class AnnotationEvaluator(TypeHintTransformer):
    """Evaluate and inspect annotations in a single pass.

    The visit starts in *annotation expression* position: `Annotated` forms and type qualifiers are unwrapped
    (and recorded) as they are encountered, and forward references are evaluated with their value visited
    in the same position (so that e.g. `Annotated['Required[int]', ...]` is handled). The first node that is
    neither is the *type expression*: from there, the visit is in type expression position, where forward
    references are evaluated and the cache key is computed.

    Args:
        globalns: The globals namespace to use during evaluation.
        localns: The locals namespace to use during evaluation.
        type_params: The type parameters in scope during evaluation.
        annotation_source: The source of the annotations to be evaluated, determining the allowed type qualifiers.
    """

    def __init__(
        self,
        globalns: GlobalsNamespace | None = None,
        localns: MappingNamespace | None = None,
        type_params: tuple[Any, ...] | None = None,
        *,
        annotation_source: AnnotationSource = AnnotationSource.ANY,
    ) -> None:
        self.globalns = globalns
        self.localns = localns
        self.type_params = type_params
        self.annotation_source = annotation_source
        self._allowed_qualifiers = annotation_source.allowed_qualifiers

        # Per-`evaluate()` call state:
        self._annotation_level = True
        self._qualifiers: set[Qualifier] = set()
        self._metadata: list[Any] = []
        self._type_expr: Any = UNKNOWN
        self._pure = True
        self._keys: list[Any] = []
        # Evaluation state, mirroring the `recursive_guard`, `owner` and `parent_fwdref`
        # arguments of `typing._eval_type()`:
        self._guard: set[str] = set()
        self._owner: Any = None
        self._parent_fwdref: ForwardRef | None = None

    def evaluate(self, annotation: Any, /) -> EvaluatedAnnotation:
        """Evaluate and inspect the annotation.

        Raises:
            ForbiddenQualifier: If a type qualifier not allowed for the annotation source is used.
            TypeError: If the annotation couldn't be evaluated.
        """
        self._annotation_level = True
        qualifiers = self._qualifiers = set()
        metadata = self._metadata = []
        self._type_expr = UNKNOWN
        self._pure = True
        keys = self._keys = []
        self._guard.clear()
        self._owner = None
        self._parent_fwdref = None

        # Apply the same conversion as `typing._type_convert()` (only relevant for the top-level annotation):
        if annotation is None:
            annotation = NoneType
        elif isinstance(annotation, str):
            # Like `typing.get_type_hints()`, assume the annotation can be in any context,
            # hence the proper `is_argument` and `is_class` arguments:
            annotation = ForwardRef(annotation, is_argument=False, is_class=True)

        try:
            full_annotation = self.visit(annotation)
        except (TypeError, RecursionError) as e:
            raise_eval_type_error(e, annotation)
        except NameError:
            # Fallback to a non-evaluating inspection of the original annotation:
            inspected = inspect_annotation(annotation, annotation_source=self.annotation_source)
            return EvaluatedAnnotation(
                annotation=annotation,
                type=inspected.type,
                qualifiers=inspected.qualifiers,
                metadata=inspected.metadata,
                evaluated=False,
                pure_key=NOT_PURE,
            )
        except InvalidExpression:
            # e.g. a bare `Generic` (`typing._eval_type()` leaves those alone; the error is raised later):
            full_annotation = eval_type(annotation, self.globalns, self.localns, self.type_params)
            inspected = inspect_annotation(full_annotation, annotation_source=self.annotation_source)
            return EvaluatedAnnotation(
                annotation=full_annotation,
                type=inspected.type,
                qualifiers=inspected.qualifiers,
                metadata=inspected.metadata,
                evaluated=True,
                pure_key=NOT_PURE,
            )

        type_expr = self._type_expr
        if self._pure and keys and not metadata and type_expr is not UNKNOWN:
            pure_key = keys[0]
        else:
            pure_key = NOT_PURE

        return EvaluatedAnnotation(
            annotation=full_annotation,
            type=type_expr,
            qualifiers=qualifiers,
            metadata=metadata,
            evaluated=True,
            pure_key=pure_key,
        )

    def _add_qualifier(self, qualifier: Qualifier) -> None:
        if qualifier not in self._allowed_qualifiers:
            raise ForbiddenQualifier(qualifier)
        self._qualifiers.add(qualifier)

    def _set_type_expr(self, type_expr: Any) -> None:
        """Leave the annotation expression position, recording the (visited) type expression."""
        self._annotation_level = False
        self._type_expr = type_expr

    # Visitor methods:

    def visit_parameterized_annotation_expr(self, annotation_expr: Any, origin: Any) -> Any:
        if self._annotation_level:
            if origin is Annotated:
                # The metadata of the outermost `Annotated` form comes last:
                self._metadata[:0] = annotation_expr.__metadata__
                annotated_type = annotation_expr.__origin__
                visited = self.visit(annotated_type)
                if visited is annotated_type:
                    return annotation_expr
                return Annotated[(visited, *annotation_expr.__metadata__)]

            qualifier = _INSPECTED_QUALIFIER_ORIGINS.get(id(origin))
            if qualifier is not None:
                self._add_qualifier(qualifier)
                (arg,) = annotation_expr.__args__
                visited = self.visit(arg)
                if visited is arg:
                    return annotation_expr
                return annotation_expr.copy_with((visited,))

            # The type expression is reached, the arguments are visited in type expression position:
            self._annotation_level = False
            visited = self._visit_type_expr_args(annotation_expr, origin)
            self._type_expr = visited
            return visited

        return self._visit_type_expr_args(annotation_expr, origin)

    def _visit_type_expr_args(self, annotation_expr: Any, origin: Any) -> Any:
        """Visit the arguments of a parameterized type expression, computing the cache key."""
        if not self._pure:
            return super().visit_parameterized_annotation_expr(annotation_expr, origin)

        tag: Any
        if id(origin) in _PURE_CONTAINER_ORIGIN_IDS:
            tag = origin
        elif origin is _UNION_ORIGIN or is_union_origin(origin):
            tag = 'union'
        elif typing_objects.is_literal(origin):
            key: list[Any] = ['literal']
            for arg in annotation_expr.__args__:
                arg_type = type(arg)
                if id(arg_type) not in _PURE_LITERAL_VALUE_TYPE_IDS:
                    self._pure = False
                    return annotation_expr
                # The type of the value is part of the key to differentiate e.g. `1` and `True`:
                key.append((arg_type, arg))
            self._keys.append(tuple(key))
            return annotation_expr
        else:
            self._pure = False
            return super().visit_parameterized_annotation_expr(annotation_expr, origin)

        keys = self._keys
        start = len(keys)
        visited = super().visit_parameterized_annotation_expr(annotation_expr, origin)
        if self._pure:
            keys[start:] = [(tag, *keys[start:])]
        return visited

    def visit_bare_annotation_expr(self, annotation_expr: Any) -> Any:
        if id(annotation_expr) in _PURE_LEAF_TYPE_IDS:
            if self._annotation_level:
                self._set_type_expr(annotation_expr)
            if self._pure:
                self._keys.append(annotation_expr)
            return annotation_expr

        if typing_objects.is_forwardref(annotation_expr) or isinstance(annotation_expr, str):
            return self.visit_forward_expr(annotation_expr)

        if self._annotation_level:
            if isinstance(annotation_expr, InitVar):
                self._add_qualifier('init_var')
                init_var_type = annotation_expr.type
                visited = self.visit(init_var_type)
                if visited is init_var_type:
                    return annotation_expr
                return InitVar(cast('type[Any]', visited))
            # `Final`, `ClassVar` and `InitVar` are type qualifiers allowed to be used as a bare annotation:
            if typing_objects.is_final(annotation_expr):
                self._add_qualifier('final')
                self._set_type_expr(UNKNOWN)
                return annotation_expr
            if typing_objects.is_classvar(annotation_expr):
                self._add_qualifier('class_var')
                self._set_type_expr(UNKNOWN)
                return annotation_expr
            if annotation_expr is InitVar:
                self._add_qualifier('init_var')
                self._set_type_expr(UNKNOWN)
                return annotation_expr
            self._set_type_expr(annotation_expr)

        self._pure = False
        return annotation_expr

    def visit_forward_expr(self, forward_expr: ForwardRef | str) -> Any:
        if isinstance(forward_expr, str):
            # A string nested in a `types.GenericAlias` (e.g. `list['int']`), which the runtime
            # doesn't convert to a `ForwardRef` instance (the same logic as `typing._make_forward_ref()`
            # is applied):
            kwargs: dict[str, Any] = {}
            parent_fwdref = self._parent_fwdref
            if parent_fwdref is not None:
                if parent_fwdref.__forward_module__ is not None:
                    kwargs['module'] = parent_fwdref.__forward_module__
                if sys.version_info >= (3, 14) and parent_fwdref.__owner__ is not None:
                    kwargs['owner'] = parent_fwdref.__owner__
            forward_expr = ForwardRef(forward_expr, **kwargs)

        guard, owner, parent_fwdref = self._guard, self._owner, self._parent_fwdref
        value = self._evaluate_forward_ref(forward_expr)
        if value is forward_expr:
            # The forward reference is being evaluated up the chain (as per the recursive guard), leave it as is:
            if self._annotation_level:
                self._set_type_expr(forward_expr)
            self._pure = False
            return forward_expr
        if value is None and self._annotation_level:
            # Same conversion as `typing._type_convert()` for the top-level annotation:
            value = NoneType
        try:
            # The evaluated value is visited in the same position (e.g. `'ClassVar[int]'` is a type qualifier form):
            return self.visit(value)
        finally:
            guard.discard(forward_expr.__forward_arg__)
            self._owner = owner
            self._parent_fwdref = parent_fwdref

    # Forward references evaluation:

    if sys.version_info >= (3, 14):

        def _evaluate_forward_ref(self, forward_ref: ForwardRef) -> Any:
            """Evaluate the forward reference (without recursing into the evaluated value).

            This mirrors the logic of `typing._eval_type()` (as called from `typing.get_type_hints()`,
            with `prefer_fwd_module=True`) and `typing.evaluate_forward_ref()`. The evaluation state
            (recursive guard, owner, parent forward reference) is updated for the visit of the evaluated
            value, and must be restored by the caller afterwards.
            """
            forward_arg = forward_ref.__forward_arg__
            if forward_arg in self._guard:
                return forward_ref

            globalns = self.globalns
            if forward_ref.__forward_module__ is not None:
                # If the forward reference has `__forward_module__` set (e.g. for `TypedDict` string annotations),
                # `ForwardRef.evaluate()` infers the globals from the module, and will probably pick
                # better than the globals we have here:
                globalns = None
                if owner_type_params := getattr(self._owner, '__type_params__', None):
                    # If there are type params on the owner, we need to add them back, because `annotationlib` won't:
                    globalns = getattr(sys.modules.get(forward_ref.__forward_module__, None), '__dict__', None)
                    if globalns is not None:
                        globalns = dict(globalns)
                        for type_param in owner_type_params:
                            globalns[type_param.__name__] = type_param

            value = forward_ref.evaluate(
                globals=globalns,
                locals=self.localns,
                type_params=self.type_params,
                owner=self._owner,
            )
            owner = self._owner if self._owner is not None else forward_ref.__owner__
            if isinstance(value, str):
                value = ForwardRef(
                    value,
                    module=forward_ref.__forward_module__,
                    owner=owner,
                    is_argument=forward_ref.__forward_is_argument__,
                    is_class=forward_ref.__forward_is_class__,
                )
            self._guard.add(forward_arg)
            self._owner = owner
            self._parent_fwdref = forward_ref
            return value

    else:

        def _evaluate_forward_ref(self, forward_ref: ForwardRef) -> Any:
            """Evaluate the forward reference.

            On Python < 3.14, the evaluation of a forward reference by the `typing` module can't be
            decoupled from the recursive evaluation of the evaluated value. As such, we defer to
            `typing._eval_type()`, which fully evaluates the forward reference.
            """
            forward_arg = forward_ref.__forward_arg__
            if forward_arg in self._guard:
                return forward_ref
            value = _stdlib_eval_type(forward_ref, self.globalns, self.localns, self.type_params)
            # Forward references still present in `value` were left as is by `typing` because of its own
            # recursive guard; the guard is mirrored so that they are left untouched by the visit as well:
            self._guard.add(forward_arg)
            return value
