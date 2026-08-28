"""Tests for the single-pass annotation evaluator (`pydantic._internal._annotation_evaluator`)."""

from __future__ import annotations

import sys
import typing
from collections.abc import Callable
from dataclasses import InitVar
from enum import Enum
from typing import Annotated, Any, ClassVar, Final, ForwardRef, Literal, NewType, Optional, TypeVar, Union

import pytest
from typing_extensions import NotRequired, ReadOnly, Required, TypedDict
from typing_inspection.introspection import UNKNOWN, AnnotationSource, ForbiddenQualifier

from pydantic import BaseModel, ConfigDict, PydanticDeprecatedSince20
from pydantic._internal._annotation_evaluator import NOT_PURE, AnnotationEvaluator, EvaluatedAnnotation

T = TypeVar('T')
UserId = NewType('UserId', int)


class Color(Enum):
    RED = 'red'


class Model(BaseModel):
    pass


def evaluate(annotation: Any, source: AnnotationSource = AnnotationSource.ANY, **ns: Any) -> EvaluatedAnnotation:
    globalns = {'Model': Model, 'T': T, 'ClassVar': ClassVar, 'Final': Final, 'Annotated': Annotated, **ns}
    return AnnotationEvaluator(globalns, {}, annotation_source=source).evaluate(annotation)


def params(*rows: Any) -> list[Any]:
    """Build unique parameter IDs (some annotations have the same `repr()`, e.g. `Optional[int]` and `int | None`)."""
    return [
        pytest.param(
            *(row if isinstance(row, tuple) else (row,)), id=f'{i}-{row[0] if isinstance(row, tuple) else row}'
        )
        for i, row in enumerate(rows)
    ]


@pytest.mark.parametrize(
    ['annotation', 'expected_key'],
    params(
        (int, int),
        (str, str),
        (None, type(None)),
        (Any, Any),
        (list[int], (list, int)),
        (typing.List[str], (list, str)),  # noqa: UP006
        (dict[str, list[int]], (dict, str, (list, int))),
        (tuple[int, ...], (tuple, int, ...)),
        (tuple[int, str], (tuple, int, str)),
        (tuple[()], (tuple,)),
        (Optional[int], ('union', int, type(None))),  # noqa: UP045
        (int | None, ('union', int, type(None))),
        (Union[int, str], ('union', int, str)),  # noqa: UP007
        (Literal[1, 'a', True, None], ('literal', (int, 1), (str, 'a'), (bool, True), (type(None), None))),
        (list[int] | dict[str, Literal['a']], ('union', (list, int), (dict, str, ('literal', (str, 'a'))))),
        (ClassVar[int], int),
        (Final[list[int]], (list, int)),
    ),
)
def test_pure_key(annotation: Any, expected_key: Any) -> None:
    evaluated = evaluate(annotation)
    assert evaluated.evaluated
    assert evaluated.pure_key == expected_key


def test_pure_key_order_matters() -> None:
    """Unions and literals compare equal irrespective of the order of their members, but the keys don't."""
    assert evaluate(int | str).pure_key != evaluate(str | int).pure_key
    assert evaluate(Literal[1, 2]).pure_key != evaluate(Literal[2, 1]).pure_key
    # `1 == True`, but the core schemas differ:
    assert evaluate(Literal[1]).pure_key != evaluate(Literal[True]).pure_key


@pytest.mark.parametrize(
    'annotation',
    params(
        Model,
        list[Model],
        Model | None,
        Annotated[int, 'meta'],  # Metadata is attached
        Final,  # Bare qualifier, unknown type
        Callable[[int], str],
        T,
        list[T],
        UserId,
        Color,
        Literal[Color.RED],
        Literal[1.5],
        typing.List,  # noqa: UP006
        type[int],
    ),
)
def test_not_pure(annotation: Any) -> None:
    assert evaluate(annotation).pure_key is NOT_PURE


def test_qualifiers_and_metadata() -> None:
    evaluated = evaluate(Final[Annotated[ClassVar[Annotated[int, 'meta_1']], 'meta_2']], AnnotationSource.CLASS)
    assert evaluated.type is int
    assert evaluated.qualifiers == {'class_var', 'final'}
    assert evaluated.metadata == ['meta_1', 'meta_2']
    assert evaluated.pure_key is NOT_PURE


@pytest.mark.parametrize(
    ['annotation', 'qualifier'],
    params(
        (Final, 'final'),
        (ClassVar, 'class_var'),
        (InitVar, 'init_var'),
    ),
)
def test_bare_qualifiers(annotation: Any, qualifier: str) -> None:
    evaluated = evaluate(annotation)
    assert evaluated.type is UNKNOWN
    assert evaluated.qualifiers == {qualifier}
    assert evaluated.pure_key is NOT_PURE


def test_typed_dict_qualifiers() -> None:
    evaluated = evaluate(Required[ReadOnly[NotRequired[int]]], AnnotationSource.TYPED_DICT)
    assert evaluated.type is int
    assert evaluated.qualifiers == {'required', 'read_only', 'not_required'}


def test_init_var() -> None:
    evaluated = evaluate(InitVar[list['int']], AnnotationSource.DATACLASS)
    assert evaluated.type == list[int]
    assert evaluated.qualifiers == {'init_var'}
    assert isinstance(evaluated.annotation, InitVar)
    assert evaluated.annotation.type == list[int]


@pytest.mark.parametrize(
    ['annotation', 'qualifier'],
    params(
        (ClassVar[int], 'class_var'),
        (Final[int], 'final'),
        (Required[int], 'required'),
        (InitVar[int], 'init_var'),
        (Final, 'final'),
    ),
)
def test_forbidden_qualifier(annotation: Any, qualifier: str) -> None:
    with pytest.raises(ForbiddenQualifier) as exc_info:
        evaluate(annotation, AnnotationSource.BARE)
    assert exc_info.value.qualifier == qualifier


def test_unchanged_annotation_is_preserved() -> None:
    """If no forward reference was evaluated, the full annotation is the original object."""
    for annotation in (int, list[int], Annotated[list[int], 'meta'], ClassVar[Annotated[int, 'meta']], Model | None):
        assert evaluate(annotation).annotation is annotation


@pytest.mark.parametrize(
    ['annotation', 'expected_annotation', 'expected_type', 'expected_key'],
    params(
        ('int', int, int, int),
        ('list[int]', list[int], list[int], (list, int)),
        (list['int'], list[int], list[int], (list, int)),
        (typing.List['int'], typing.List[int], typing.List[int], (list, int)),  # noqa: UP006
        (dict['str', list['int']], dict[str, list[int]], dict[str, list[int]], (dict, str, (list, int))),
        (Optional['int'], Optional[int], Optional[int], ('union', int, type(None))),  # noqa: UP045, F821
        ('int | None', int | None, int | None, ('union', int, type(None))),
        (Annotated['int', 'meta'], Annotated[int, 'meta'], int, NOT_PURE),
        (ClassVar['int'], ClassVar[int], int, int),
        ('ClassVar[int]', ClassVar[int], int, int),
        (Annotated['ClassVar[int]', 'meta'], Annotated[ClassVar[int], 'meta'], int, NOT_PURE),
        ("Annotated['ClassVar[list[int]]', 'meta']", Annotated[ClassVar[list[int]], 'meta'], list[int], NOT_PURE),
        ("Final[Annotated['int', 'meta']]", Final[Annotated[int, 'meta']], int, NOT_PURE),
        ('Model', Model, Model, NOT_PURE),
        (list['Model'], list[Model], list[Model], NOT_PURE),
        ('None', type(None), type(None), type(None)),
        (None, type(None), type(None), type(None)),
        # (Before Python 3.14, `typing` converts nested `None` forward references to `NoneType`):
        *(
            [(list['None'], list[None], list[None], (list, None))]
            if sys.version_info >= (3, 14)
            else [(list['None'], list[type(None)], list[type(None)], (list, type(None)))]
        ),
        (Literal['a'], Literal['a'], Literal['a'], ('literal', (str, 'a'))),  # Strings in literals aren't evaluated
    ),
)
def test_forward_references(annotation: Any, expected_annotation: Any, expected_type: Any, expected_key: Any) -> None:
    evaluated = evaluate(annotation, AnnotationSource.CLASS)
    assert evaluated.evaluated
    assert evaluated.annotation == expected_annotation
    assert evaluated.type == expected_type
    assert evaluated.pure_key == expected_key


def test_forward_reference_locals_priority() -> None:
    evaluator = AnnotationEvaluator({'A': int}, {'A': str})
    assert evaluator.evaluate('A').type is str
    assert evaluator.evaluate(list['A']).type == list[str]  # noqa: F821


def test_type_params() -> None:
    evaluator = AnnotationEvaluator({}, {}, type_params=(T,))
    evaluated = evaluator.evaluate('list[T]')
    assert evaluated.type == list[T]
    assert evaluated.pure_key is NOT_PURE


def test_nested_string_forward_reference() -> None:
    evaluated = evaluate("list['Model']")
    assert evaluated.type == list[Model]
    assert evaluated.annotation == list[Model]


def test_forward_reference_to_string() -> None:
    """A forward reference evaluating to a string is evaluated again."""
    evaluated = evaluate('Alias', Alias='int')
    assert evaluated.type is int


def test_recursive_forward_reference() -> None:
    """Mirrors the recursive guard of `typing._eval_type()` for implicit recursive aliases."""
    evaluator = AnnotationEvaluator({'Rec': list['Rec']}, {})  # noqa: F821
    evaluated = evaluator.evaluate('Rec')
    assert evaluated.evaluated
    assert evaluated.type == list[ForwardRef('Rec')]
    assert evaluated.pure_key is NOT_PURE
    if sys.version_info >= (3, 14):
        assert evaluated.type == typing.evaluate_forward_ref(ForwardRef('Rec'), globals={'Rec': list['Rec']})  # noqa: F821


@pytest.mark.parametrize(
    ['annotation', 'expected_type', 'expected_qualifiers', 'expected_metadata'],
    params(
        ('Undefined', ForwardRef('Undefined', is_argument=False, is_class=True), set(), []),
        (list['Undefined'], list['Undefined'], set(), []),  # noqa: F821
        (Annotated['Undefined', 'meta'], ForwardRef('Undefined', is_class=True), set(), ['meta']),  # noqa: F821
        (ClassVar['Undefined'], ForwardRef('Undefined', is_class=True), {'class_var'}, []),  # noqa: F821
        ('ClassVar[Undefined]', ForwardRef('ClassVar[Undefined]', is_argument=False, is_class=True), set(), []),
        (Annotated[list['Undefined'], 'meta'], list['Undefined'], set(), ['meta']),  # noqa: F821
    ),
)
def test_undefined_name(
    annotation: Any, expected_type: Any, expected_qualifiers: set[str], expected_metadata: list[Any]
) -> None:
    """When a `NameError` is raised, the (unevaluated) annotation is still inspected, without evaluation."""
    evaluated = evaluate(annotation, AnnotationSource.CLASS)
    assert not evaluated.evaluated
    assert evaluated.type == expected_type
    assert evaluated.qualifiers == expected_qualifiers
    assert evaluated.metadata == expected_metadata
    assert evaluated.pure_key is NOT_PURE
    assert evaluated.annotation == (
        ForwardRef(annotation, is_argument=False, is_class=True) if isinstance(annotation, str) else annotation
    )


def test_invalid_forward_reference() -> None:
    with pytest.raises(SyntaxError):
        evaluate('1 +')
    with pytest.raises(TypeError):
        evaluate(list["1 + 'a'"])  # noqa: F821


def test_forward_module() -> None:
    """Forward references with a module set (e.g. `TypedDict` string annotations) use the module namespace."""

    class TD(TypedDict):
        a: 'Model'  # noqa: UP037

    fwd_ref = TD.__annotations__['a']
    if not isinstance(fwd_ref, ForwardRef):
        pytest.skip('String annotations are not converted to forward references')
    assert fwd_ref.__forward_module__ == __name__
    # The provided globals are ignored in favor of the module's namespace:
    evaluated = AnnotationEvaluator({'Model': int}, {}).evaluate(fwd_ref)
    assert evaluated.type is Model


@pytest.mark.skipif(sys.version_info < (3, 14), reason='Requires PEP 649 (deferred annotations)')
def test_deferred_annotations_forward_references() -> None:
    """Partially evaluated annotations (containing `ForwardRef` instances from the *forward ref* format)."""
    import annotationlib

    class M:
        a: list[Undefined]  # noqa: F821
        b: Undefined | None  # noqa: F821

    annotations = annotationlib.get_annotations(M, format=annotationlib.Format.FORWARDREF)
    evaluator = AnnotationEvaluator({}, {'Undefined': int})
    assert evaluator.evaluate(annotations['a']).type == list[int]
    assert evaluator.evaluate(annotations['b']).type == int | None

    evaluator = AnnotationEvaluator({}, {})
    assert not evaluator.evaluate(annotations['a']).evaluated
    assert not evaluator.evaluate(annotations['b']).evaluated


def test_pure_schema_cache() -> None:
    from pydantic._internal import _generate_schema

    class Model1(BaseModel):
        a: list[int]
        b: Annotated[list[int], 'meta']  # Metadata attached: not cached

    class Model2(BaseModel):
        a: list[int] = []

    assert Model1.model_fields['a']._pure_key == (list[int], (list, int))
    assert Model1.model_fields['b']._pure_key is None
    assert Model2.model_fields['a']._pure_key == (list[int], (list, int))
    assert (list, int) in _generate_schema._pure_schema_cache

    # Cached schemas are handed out as copies:
    schema_1 = Model1.__pydantic_core_schema__['schema']['fields']['a']['schema']
    schema_2 = Model2.__pydantic_core_schema__['schema']['fields']['a']['schema']['schema']
    assert schema_1 == schema_2 == {'type': 'list', 'items_schema': {'type': 'int'}}
    assert schema_1 is not schema_2
    assert schema_1['items_schema'] is not schema_2['items_schema']
    assert schema_1 is not _generate_schema._pure_schema_cache[(list, int)]

    assert Model1(a=[1], b=[2]).a == [1]
    assert Model2(a=['3']).a == [3]


def test_pure_schema_cache_mutated_annotation() -> None:
    """The cache key is invalidated if the `annotation` attribute of the field is mutated."""

    class Model(BaseModel):
        a: int

    Model.model_fields['a'].annotation = int | None
    Model.model_fields['a'].default = None
    Model.model_rebuild(force=True)

    assert Model.model_fields['a']._pure_key == (int, int)
    assert Model().a is None
    assert Model(a=None).a is None
    assert Model(a=1).a == 1


def test_pure_schema_cache_json_encoders() -> None:
    """The (deprecated) `json_encoders` configuration is applied to core schemas: the cache is bypassed."""

    class Model1(BaseModel):
        a: int

    with pytest.warns(PydanticDeprecatedSince20):

        class Model2(BaseModel):
            model_config = ConfigDict(json_encoders={int: lambda v: 'encoded'})

            a: int

    assert Model1(a=1).model_dump_json() == '{"a":1}'
    assert Model2(a=1).model_dump_json() == '{"a":"encoded"}'


def test_evaluator_reusable() -> None:
    """The per-call state is properly reset between calls."""
    evaluator = AnnotationEvaluator({'Rec': list['Rec'], 'Model': Model}, {})  # noqa: F821
    assert evaluator.evaluate('Rec').pure_key is NOT_PURE
    assert evaluator.evaluate(list['int']).pure_key == (list, int)
    assert evaluator.evaluate(Model).pure_key is NOT_PURE
    assert evaluator.evaluate(int).pure_key is int
    # The recursive guard is reset:
    assert evaluator.evaluate('Rec').type == list[ForwardRef('Rec')]
