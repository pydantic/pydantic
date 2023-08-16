from __future__ import annotations

import dataclasses
from collections import defaultdict
from copy import copy
from functools import partial
from typing import Any, Iterable

import annotated_types as at
from pydantic_core import CoreSchema, PydanticCustomError
from pydantic_core import core_schema as cs

from . import _validators
from ._fields import PydanticGeneralMetadata, PydanticMetadata

STRICT = {'strict'}
SEQUENCE_CONSTRAINTS = {'min_length', 'max_length'}
INEQUALITY = {'le', 'ge', 'lt', 'gt'}
NUMERIC_CONSTRAINTS = {'multiple_of', 'allow_inf_nan', *INEQUALITY}

STR_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT, 'strip_whitespace', 'to_lower', 'to_upper', 'pattern'}
BYTES_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}

LIST_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
TUPLE_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
SET_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
DICT_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}
GENERATOR_CONSTRAINTS = {*SEQUENCE_CONSTRAINTS, *STRICT}

FLOAT_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
INT_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
BOOL_CONSTRAINTS = STRICT

DATE_TIME_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
TIMEDELTA_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}
TIME_CONSTRAINTS = {*NUMERIC_CONSTRAINTS, *STRICT}

UNION_CONSTRAINTS = {'union_mode'}
URL_CONSTRAINTS = {
    'max_length',
    'allowed_schemes',
    'host_required',
    'default_host',
    'default_port',
    'default_path',
}

TEXT_SCHEMA_TYPES = ('str', 'bytes', 'url', 'multi-host-url')
SEQUENCE_SCHEMA_TYPES = ('list', 'tuple', 'set', 'frozenset', 'generator', *TEXT_SCHEMA_TYPES)
NUMERIC_SCHEMA_TYPES = ('float', 'int', 'date', 'time', 'timedelta', 'datetime')

CONSTRAINTS_TO_ALLOWED_SCHEMAS: dict[str, set[str]] = defaultdict(set)
for constraint in STR_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(TEXT_SCHEMA_TYPES)
for constraint in BYTES_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('bytes',))
for constraint in LIST_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('list',))
for constraint in TUPLE_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('tuple',))
for constraint in SET_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('set', 'frozenset'))
for constraint in DICT_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('dict',))
for constraint in GENERATOR_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('generator',))
for constraint in FLOAT_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('float',))
for constraint in INT_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('int',))
for constraint in DATE_TIME_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('date', 'time', 'datetime'))
for constraint in TIMEDELTA_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('timedelta',))
for constraint in TIME_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('time',))
for schema_type in (*TEXT_SCHEMA_TYPES, *SEQUENCE_SCHEMA_TYPES, *NUMERIC_SCHEMA_TYPES, 'typed-dict', 'model'):
    CONSTRAINTS_TO_ALLOWED_SCHEMAS['strict'].add(schema_type)
for constraint in UNION_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('union',))
for constraint in URL_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('url', 'multi-host-url'))
for constraint in BOOL_CONSTRAINTS:
    CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint].update(('bool',))


def expand_grouped_metadata(annotations: Iterable[Any]) -> Iterable[Any]:
    """Expand the annotations.

    Args:
        annotations: An iterable of annotations.

    Returns:
        An iterable of expanded annotations.

    Example:
        ```py
        from annotated_types import Ge, Len

        from pydantic._internal._known_annotated_metadata import expand_grouped_metadata

        print(list(expand_grouped_metadata([Ge(4), Len(5)])))
        #> [Ge(ge=4), MinLen(min_length=5)]
        ```
    """
    from pydantic.fields import FieldInfo  # circular import

    for annotation in annotations:
        if isinstance(annotation, at.GroupedMetadata):
            yield from annotation
        elif isinstance(annotation, FieldInfo):
            yield from annotation.metadata
            # this is a bit problematic in that it results in duplicate metadata
            # all of our "consumers" can handle it, but it is not ideal
            # we probably should split up FieldInfo into:
            # - annotated types metadata
            # - individual metadata known only to Pydantic
            annotation = copy(annotation)
            annotation.metadata = []
            yield annotation
        else:
            yield annotation


def apply_known_metadata(annotation: Any, schema: CoreSchema) -> CoreSchema | None:  # noqa: C901
    """Apply `annotation` to `schema` if it is an annotation we know about (Gt, Le, etc.).
    Otherwise return `None`.

    This does not handle all known annotations. If / when it does, it can always
    return a CoreSchema and return the unmodified schema if the annotation should be ignored.

    Assumes that GroupedMetadata has already been expanded via `expand_grouped_metadata`.

    Args:
        annotation: The annotation.
        schema: The schema.

    Returns:
        An updated schema with annotation if it is an annotation we know about, `None` otherwise.

    Raises:
        PydanticCustomError: If `Predicate` fails.
    """
    schema = schema.copy()
    schema_update, other_metadata = collect_known_metadata([annotation])
    schema_type = schema['type']
    for constraint, value in schema_update.items():
        if constraint not in CONSTRAINTS_TO_ALLOWED_SCHEMAS:
            raise ValueError(f'Unknown constraint {constraint}')
        allowed_schemas = CONSTRAINTS_TO_ALLOWED_SCHEMAS[constraint]

        if schema_type in allowed_schemas:
            if constraint == 'union_mode' and schema_type == 'union':
                schema['mode'] = value  # type: ignore  # schema is UnionSchema
            else:
                schema[constraint] = value
            continue

        if constraint == 'allow_inf_nan' and value is False:
            return cs.no_info_after_validator_function(
                _validators.forbid_inf_nan_check,
                schema,
            )
        elif constraint == 'pattern':
            # insert a str schema to make sure the regex engine matches
            return cs.chain_schema(
                [
                    schema,
                    cs.str_schema(pattern=value),
                ]
            )
        elif constraint == 'gt':
            return cs.no_info_after_validator_function(
                partial(_validators.greater_than_validator, gt=value),
                schema,
            )
        elif constraint == 'ge':
            return cs.no_info_after_validator_function(
                partial(_validators.greater_than_or_equal_validator, ge=value),
                schema,
            )
        elif constraint == 'lt':
            return cs.no_info_after_validator_function(
                partial(_validators.less_than_validator, lt=value),
                schema,
            )
        elif constraint == 'le':
            return cs.no_info_after_validator_function(
                partial(_validators.less_than_or_equal_validator, le=value),
                schema,
            )
        elif constraint == 'multiple_of':
            return cs.no_info_after_validator_function(
                partial(_validators.multiple_of_validator, multiple_of=value),
                schema,
            )
        elif constraint == 'min_length':
            return cs.no_info_after_validator_function(
                partial(_validators.min_length_validator, min_length=value),
                schema,
            )
        elif constraint == 'max_length':
            return cs.no_info_after_validator_function(
                partial(_validators.max_length_validator, max_length=value),
                schema,
            )
        elif constraint == 'strip_whitespace':
            return cs.chain_schema(
                [
                    schema,
                    cs.str_schema(strip_whitespace=True),
                ]
            )
        elif constraint == 'to_lower':
            return cs.chain_schema(
                [
                    schema,
                    cs.str_schema(to_lower=True),
                ]
            )
        elif constraint == 'to_upper':
            return cs.chain_schema(
                [
                    schema,
                    cs.str_schema(to_upper=True),
                ]
            )
        elif constraint == 'min_length':
            return cs.no_info_after_validator_function(
                partial(_validators.min_length_validator, min_length=annotation.min_length),
                schema,
            )
        elif constraint == 'max_length':
            return cs.no_info_after_validator_function(
                partial(_validators.max_length_validator, max_length=annotation.max_length),
                schema,
            )
        else:
            raise RuntimeError(f'Unable to apply constraint {constraint} to schema {schema_type}')

    for annotation in other_metadata:
        if isinstance(annotation, at.Gt):
            return cs.no_info_after_validator_function(
                partial(_validators.greater_than_validator, gt=annotation.gt),
                schema,
            )
        elif isinstance(annotation, at.Ge):
            return cs.no_info_after_validator_function(
                partial(_validators.greater_than_or_equal_validator, ge=annotation.ge),
                schema,
            )
        elif isinstance(annotation, at.Lt):
            return cs.no_info_after_validator_function(
                partial(_validators.less_than_validator, lt=annotation.lt),
                schema,
            )
        elif isinstance(annotation, at.Le):
            return cs.no_info_after_validator_function(
                partial(_validators.less_than_or_equal_validator, le=annotation.le),
                schema,
            )
        elif isinstance(annotation, at.MultipleOf):
            return cs.no_info_after_validator_function(
                partial(_validators.multiple_of_validator, multiple_of=annotation.multiple_of),
                schema,
            )
        elif isinstance(annotation, at.MinLen):
            return cs.no_info_after_validator_function(
                partial(_validators.min_length_validator, min_length=annotation.min_length),
                schema,
            )
        elif isinstance(annotation, at.MaxLen):
            return cs.no_info_after_validator_function(
                partial(_validators.max_length_validator, max_length=annotation.max_length),
                schema,
            )
        elif isinstance(annotation, at.Predicate):
            predicate_name = f'{annotation.func.__qualname__} ' if hasattr(annotation.func, '__qualname__') else ''

            def val_func(v: Any) -> Any:
                # annotation.func may also raise an exception, let it pass through
                if not annotation.func(v):
                    raise PydanticCustomError(
                        'predicate_failed',
                        f'Predicate {predicate_name}failed',  # type: ignore
                    )
                return v

            return cs.no_info_after_validator_function(val_func, schema)
        # ignore any other unknown metadata
        return None

    return schema


def collect_known_metadata(annotations: Iterable[Any]) -> tuple[dict[str, Any], list[Any]]:
    """Split `annotations` into known metadata and unknown annotations.

    Args:
        annotations: An iterable of annotations.

    Returns:
        A tuple contains a dict of known metadata and a list of unknown annotations.

    Example:
        ```py
        from annotated_types import Gt, Len

        from pydantic._internal._known_annotated_metadata import collect_known_metadata

        print(collect_known_metadata([Gt(1), Len(42), ...]))
        #> ({'gt': 1, 'min_length': 42}, [Ellipsis])
        ```
    """
    annotations = expand_grouped_metadata(annotations)

    res: dict[str, Any] = {}
    remaining: list[Any] = []
    for annotation in annotations:
        # Do we really want to consume any `BaseMetadata`?
        # It does let us give a better error when there is an annotation that doesn't apply
        # But it seems dangerous!
        if isinstance(annotation, PydanticGeneralMetadata):
            res.update(annotation.__dict__)
        elif isinstance(annotation, PydanticMetadata):
            res.update(dataclasses.asdict(annotation))  # type: ignore[call-overload]
        elif isinstance(annotation, (at.MinLen, at.MaxLen, at.Gt, at.Ge, at.Lt, at.Le, at.MultipleOf)):
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
    """A small utility function to validate that the given metadata can be applied to the target.
    More than saving lines of code, this gives us a consistent error message for all of our internal implementations.

    Args:
        metadata: A dict of metadata.
        allowed: An iterable of allowed metadata.
        source_type: The source type.

    Raises:
        TypeError: If there is metadatas that can't be applied on source type.
    """
    unknown = metadata.keys() - set(allowed)
    if unknown:
        raise TypeError(
            f'The following constraints cannot be applied to {source_type!r}: {", ".join([f"{k!r}" for k in unknown])}'
        )
