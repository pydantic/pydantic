from __future__ import annotations

import dataclasses
from functools import partial
from typing import Any, Iterable

import annotated_types as at
from pydantic_core import CoreSchema
from pydantic_core import core_schema as cs

from . import _validators
from ._fields import PydanticGeneralMetadata, PydanticMetadata

STRICT = {'strict'}
SEQUENCE_CONSTRAINTS = {'min_length', 'max_length'}
INEQUALITY = {'le', 'ge', 'lt', 'gt'}
NUMERIC_CONSTRAINTS = {'multiple_of', 'allow_inf_nan', *INEQUALITY}

STR_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT, 'strip_whitespace', 'to_lower', 'to_upper'}
BYTES_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}

LIST_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
TUPLE_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
SET_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
DICT_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
GENERATOR_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}

FLOAT_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
INT_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}

DATE_TIME_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
TIMEDELTA_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
TIME_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}

TEXT_SCHEMA_TYPES = ('str', 'bytes', 'url', 'multi-host-url')
SEQUENCE_SCHEMA_TYPES = ('list', 'tuple', 'set', 'frozenset', 'generator', *TEXT_SCHEMA_TYPES)
NUMERIC_SCHEMA_TYPES = ('float', 'int', 'date', 'time', 'timedelta', 'datetime')


def apply_known_metadata(annotation: Any, schema: CoreSchema) -> CoreSchema:  # noqa: C901
    """
    Apply `annotation` to `schema` if it is an annotation we know about (Gt, Le, etc.).
    Otherwise return `None`.

    This does not handle all known annotations. If / when it does, it can always
    return a CoreSchema and return the unmodified schema if the annotation should be ignored.
    """
    schema = schema.copy()
    schema_update, _ = collect_known_metadata([annotation])
    if isinstance(annotation, at.GroupedMetadata):
        for constraint in annotation:
            schema = apply_known_metadata(constraint, schema) or schema
    elif isinstance(annotation, at.Gt):
        if schema['type'] in NUMERIC_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.greater_than_validator, gt=annotation.gt),
                schema,
            )
    elif isinstance(annotation, at.Ge):
        if schema['type'] in NUMERIC_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.greater_than_or_equal_validator, ge=annotation.ge),
                schema,
            )
    elif isinstance(annotation, at.Lt):
        if schema['type'] in NUMERIC_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.less_than_validator, lt=annotation.lt),
                schema,
            )
    elif isinstance(annotation, at.Le):
        if schema['type'] in NUMERIC_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.less_than_or_equal_validator, le=annotation.le),
                schema,
            )
    elif isinstance(annotation, at.MultipleOf):
        if schema['type'] in NUMERIC_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.multiple_of_validator, multiple_of=annotation.multiple_of),
                schema,
            )
    elif isinstance(annotation, at.MinLen):
        if schema['type'] in SEQUENCE_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.min_length_validator, min_length=annotation.min_length),
                schema,
            )
    elif isinstance(annotation, at.MaxLen):
        if schema['type'] in SEQUENCE_SCHEMA_TYPES:
            schema.update(schema_update)  # type: ignore
        else:
            return cs.no_info_after_validator_function(
                partial(_validators.max_length_validator, max_length=annotation.max_length),
                schema,
            )
    elif isinstance(annotation, at.Predicate):

        def val_func(v: Any) -> Any:
            # annotation.func may also raise an exception, let it pass through
            assert annotation.func(v), f'Predicate {annotation.func} failed'

        return cs.no_info_after_validator_function(val_func, schema)

    # for all other annotations just update the schema
    # this includes things like `strict` which apply to pretty much every schema
    schema.update(schema_update)  # type: ignore

    return schema


def collect_known_metadata(annotations: Iterable[Any]) -> tuple[dict[str, Any], list[Any]]:
    """
    Split `annotations` into known metadata and unknown annotations.

    For example `[Gt(1), Len(42), Unknown()]` -> `({'gt': 1, 'min_length': 42}, [Unknown()])`.
    """
    from pydantic.fields import FieldInfo  # circular import

    res: dict[str, Any] = {}
    remaining: list[Any] = []
    for annotation in annotations:
        if isinstance(annotation, at.GroupedMetadata):
            m, r = collect_known_metadata(list(annotation))
            res.update(m)
            remaining.extend(r)
        elif isinstance(annotation, FieldInfo):
            for sub in annotation.metadata:
                m, r = collect_known_metadata([sub])
                res.update(m)
                remaining.extend(r)
        # Do we really want to consume any `BaseMetadata`?
        # It does let us give a better error when there is an annotation that doesn't apply
        # But it seems dangerous!
        elif isinstance(annotation, PydanticGeneralMetadata):
            res.update(annotation.__dict__)
        elif isinstance(annotation, (at.BaseMetadata, PydanticMetadata)):
            res.update(dataclasses.asdict(annotation))  # type: ignore[call-overload]
        elif isinstance(annotation, type) and issubclass(annotation, PydanticMetadata):
            # also support PydanticMetadata classes being used without initialisation,
            # e.g. `Annotated[int, Strict]` as well as `Annotated[int, Strict()]`
            res.update({k: v for k, v in vars(annotation).items() if not k.startswith('_')})
        else:
            remaining.append(annotation)
    # Nones can sneak in but pydantic-core will reject them
    # it'd be nice to clean things up so we don't put in None (we probably don't _need_ to, it was just easier)
    # but this is simple enough to kick that can down the road
    res = {k: v for k, v in res.items() if v is not None}
    return res, remaining


def check_metadata(metadata: dict[str, Any], allowed: Iterable[str], source_type: Any) -> None:
    """
    A small utility function to validate that the given metadata can be applied to the target.
    More than saving lines of code, this gives us a consistent error message for all of our internal implementations.
    """
    unknown = metadata.keys() - set(allowed)
    if unknown:
        raise TypeError(
            f'The following constraints cannot be applied to {source_type!r}: {", ".join([f"{k!r}" for k in unknown])}'
        )
