"""Tests for `ModelFieldsSet`, the set used to track the fields explicitly set on a model instance."""

from __future__ import annotations

import copy
import pickle
from collections.abc import MutableSet, Set
from typing import Any

import pytest

from pydantic_core import ModelFieldsSet, SchemaSerializer, SchemaValidator, core_schema


class MyModel:
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'


def make_validator(extra_behavior: str = 'ignore', **kwargs: Any) -> SchemaValidator:
    return SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.int_schema()),
                    'b': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=2)),
                    'c': core_schema.model_field(
                        core_schema.with_default_schema(core_schema.int_schema(), default=3),
                        validation_alias='c_alias',
                    ),
                },
                extra_behavior=extra_behavior,
                **kwargs,
            ),
        )
    )


@pytest.fixture
def fields_set() -> ModelFieldsSet:
    """A fields set with `a` and `c` set, and an `x` extra key."""
    m = make_validator('allow').validate_python({'a': 1, 'c_alias': 3, 'x': 10})
    return m.__pydantic_fields_set__


def test_validation_creates_model_fields_set(fields_set: ModelFieldsSet) -> None:
    assert type(fields_set) is ModelFieldsSet
    assert fields_set == {'a', 'c', 'x'}
    # Known fields first, in definition order, then extra keys:
    assert list(fields_set) == ['a', 'c', 'x']
    assert len(fields_set) == 3


def test_validation_json() -> None:
    m = make_validator('allow').validate_json('{"a": 1, "c_alias": 3, "x": 10}')
    assert type(m.__pydantic_fields_set__) is ModelFieldsSet
    assert m.__pydantic_fields_set__ == {'a', 'c', 'x'}
    assert list(m.__pydantic_fields_set__) == ['a', 'c', 'x']


@pytest.mark.parametrize('mode', ['python', 'json'])
def test_no_extra(mode: str) -> None:
    v = make_validator()
    data = {'a': 1, 'x': 10}
    m = v.validate_python(data) if mode == 'python' else v.validate_json('{"a": 1, "x": 10}')
    assert m.__pydantic_fields_set__ == {'a'}
    assert 'x' not in m.__pydantic_fields_set__


def test_extra_key_equal_to_field_name() -> None:
    """When a field has an alias, an extra key can be equal to a field name.

    Note that this only applies to Python validation: when validating JSON, such keys are ignored.
    """
    v = make_validator('allow')
    m = v.validate_python({'c': 7, 'a': 1})
    assert m.__dict__ == {'a': 1, 'b': 2, 'c': 3}
    assert m.__pydantic_extra__ == {'c': 7}
    assert m.__pydantic_fields_set__ == {'a', 'c'}
    assert list(m.__pydantic_fields_set__) == ['a', 'c']

    m.__pydantic_fields_set__.discard('c')
    assert m.__pydantic_fields_set__ == {'a'}


def test_extra_keys_validator_transforming_key() -> None:
    """Extra keys transformed by the extra keys validator can be equal to a field name."""
    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {'a': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=0))},
                extra_behavior='allow',
                extras_keys_schema=core_schema.no_info_plain_validator_function(lambda k: k.removeprefix('_')),
            ),
        )
    )
    m = v.validate_python({'_a': 1})
    assert m.__pydantic_extra__ == {'a': 1}
    assert m.__pydantic_fields_set__ == {'a'}
    assert list(m.__pydantic_fields_set__) == ['a']


def test_abc_registration(fields_set: ModelFieldsSet) -> None:
    assert isinstance(fields_set, MutableSet)
    assert isinstance(fields_set, Set)
    assert not isinstance(fields_set, set)
    assert not issubclass(ModelFieldsSet, set)


def test_repr(fields_set: ModelFieldsSet) -> None:
    """The representation is the same as the one of `set`."""
    assert repr(fields_set) == "{'a', 'c', 'x'}"
    assert repr(ModelFieldsSet()) == 'set()'


def test_unhashable(fields_set: ModelFieldsSet) -> None:
    with pytest.raises(TypeError, match='unhashable type'):
        hash(fields_set)


def test_contains(fields_set: ModelFieldsSet) -> None:
    assert 'a' in fields_set
    assert 'c' in fields_set
    assert 'x' in fields_set
    assert 'b' not in fields_set
    assert 'unknown' not in fields_set
    assert 1 not in fields_set
    assert None not in fields_set
    # Non-interned strings:
    assert ''.join(['a']) in fields_set
    assert ''.join(['b']) not in fields_set
    assert '\udcff' not in fields_set


def test_equality(fields_set: ModelFieldsSet) -> None:
    assert fields_set == {'a', 'c', 'x'}
    assert {'a', 'c', 'x'} == fields_set
    assert fields_set == frozenset({'a', 'c', 'x'})
    assert fields_set == {'a': 1, 'c': 2, 'x': 3}.keys()
    assert fields_set == fields_set.copy()
    assert fields_set != {'a'}
    assert {'a'} != fields_set
    assert fields_set != {'a', 'c', 'x', 'y'}
    assert fields_set != 'acx'
    assert fields_set != ['a', 'c', 'x']
    assert not (fields_set == ['a', 'c', 'x'])


def test_comparisons(fields_set: ModelFieldsSet) -> None:
    assert fields_set <= {'a', 'c', 'x'}
    assert fields_set <= {'a', 'c', 'x', 'y'}
    assert not fields_set < {'a', 'c', 'x'}
    assert fields_set < {'a', 'c', 'x', 'y'}
    assert fields_set >= {'a', 'c', 'x'}
    assert fields_set >= {'a'}
    assert not fields_set > {'a', 'c', 'x'}
    assert fields_set > {'a'}
    assert not fields_set <= {'a'}
    assert not fields_set >= {'y'}

    # Reflected:
    assert {'a'} <= fields_set
    assert {'a'} < fields_set
    assert {'a', 'c', 'x', 'y'} >= fields_set
    assert {'a', 'c', 'x', 'y'} > fields_set
    assert fields_set <= fields_set
    assert not fields_set < fields_set

    with pytest.raises(TypeError):
        fields_set < ['a']
    with pytest.raises(TypeError):
        fields_set >= 'a'


def test_copy(fields_set: ModelFieldsSet) -> None:
    for copied in (fields_set.copy(), copy.copy(fields_set), copy.deepcopy(fields_set)):
        assert type(copied) is ModelFieldsSet
        assert copied is not fields_set
        assert copied == fields_set
        copied.add('b')
        assert 'b' not in fields_set
        copied.add('y')
        assert 'y' not in fields_set


def test_pickle(fields_set: ModelFieldsSet) -> None:
    unpickled = pickle.loads(pickle.dumps(fields_set))
    assert type(unpickled) is ModelFieldsSet
    assert unpickled == fields_set
    assert list(unpickled) == ['a', 'c', 'x']
    # The field names are preserved:
    unpickled.add('b')
    assert list(unpickled) == ['a', 'b', 'c', 'x']


def test_constructor() -> None:
    fields_set = ModelFieldsSet(['b', 'y'], field_names=['a', 'b'])
    assert fields_set == {'b', 'y'}
    fields_set.add('a')
    assert list(fields_set) == ['a', 'b', 'y']

    assert ModelFieldsSet() == set()
    assert ModelFieldsSet(['a']) == {'a'}
    assert ModelFieldsSet(field_names=['a']) == set()

    with pytest.raises(TypeError):
        ModelFieldsSet([1])
    with pytest.raises(TypeError):
        ModelFieldsSet(field_names=[1])


def test_add(fields_set: ModelFieldsSet) -> None:
    fields_set.add('b')
    assert list(fields_set) == ['a', 'b', 'c', 'x']
    fields_set.add('b')
    assert list(fields_set) == ['a', 'b', 'c', 'x']
    fields_set.add('y')
    assert fields_set == {'a', 'b', 'c', 'x', 'y'}
    fields_set.add('y')
    assert len(fields_set) == 5

    with pytest.raises(TypeError, match='ModelFieldsSet elements must be strings, got int'):
        fields_set.add(1)


def test_discard_remove(fields_set: ModelFieldsSet) -> None:
    fields_set.discard('a')
    assert fields_set == {'c', 'x'}
    fields_set.discard('a')
    fields_set.discard('unknown')
    fields_set.discard(1)
    fields_set.discard('x')
    assert fields_set == {'c'}

    fields_set.remove('c')
    assert fields_set == set()
    with pytest.raises(KeyError, match="'c'"):
        fields_set.remove('c')
    with pytest.raises(KeyError):
        fields_set.remove(1)


def test_pop(fields_set: ModelFieldsSet) -> None:
    assert fields_set.pop() == 'a'
    assert fields_set.pop() == 'c'
    assert fields_set.pop() == 'x'
    with pytest.raises(KeyError, match='pop from an empty set'):
        fields_set.pop()


def test_clear(fields_set: ModelFieldsSet) -> None:
    fields_set.clear()
    assert fields_set == set()
    assert len(fields_set) == 0
    assert list(fields_set) == []
    fields_set.add('b')
    assert fields_set == {'b'}


def test_update(fields_set: ModelFieldsSet) -> None:
    fields_set.update()
    assert fields_set == {'a', 'c', 'x'}
    fields_set.update(['b'], {'y'}, 'z')
    assert fields_set == {'a', 'b', 'c', 'x', 'y', 'z'}
    fields_set.update(fields_set)
    assert fields_set == {'a', 'b', 'c', 'x', 'y', 'z'}
    with pytest.raises(TypeError):
        fields_set.update(1)
    with pytest.raises(TypeError):
        fields_set.update([1])


def test_intersection_update(fields_set: ModelFieldsSet) -> None:
    fields_set.intersection_update(['a', 'x', 'y'], {'a', 'x'})
    assert fields_set == {'a', 'x'}
    fields_set.intersection_update(fields_set)
    assert fields_set == {'a', 'x'}
    fields_set.intersection_update([1])
    assert fields_set == set()


def test_difference_update(fields_set: ModelFieldsSet) -> None:
    fields_set.difference_update(['a', 'y', 1], {'x'})
    assert fields_set == {'c'}
    fields_set.difference_update(fields_set)
    assert fields_set == set()


def test_symmetric_difference_update(fields_set: ModelFieldsSet) -> None:
    fields_set.symmetric_difference_update(['a', 'b', 'b', 'y'])
    assert fields_set == {'b', 'c', 'x', 'y'}
    fields_set.symmetric_difference_update(fields_set)
    assert fields_set == set()


def test_union(fields_set: ModelFieldsSet) -> None:
    result = fields_set.union(['b'], {'y'})
    assert type(result) is ModelFieldsSet
    assert result == {'a', 'b', 'c', 'x', 'y'}
    assert fields_set == {'a', 'c', 'x'}
    assert fields_set.union() == fields_set
    assert fields_set.union(fields_set) == fields_set


def test_intersection(fields_set: ModelFieldsSet) -> None:
    result = fields_set.intersection(['a', 'b', 'x'], {'x', 'a'})
    assert type(result) is ModelFieldsSet
    assert result == {'a', 'x'}
    assert fields_set == {'a', 'c', 'x'}


def test_difference(fields_set: ModelFieldsSet) -> None:
    result = fields_set.difference(['a'], {'x'})
    assert type(result) is ModelFieldsSet
    assert result == {'c'}
    assert fields_set == {'a', 'c', 'x'}


def test_symmetric_difference(fields_set: ModelFieldsSet) -> None:
    result = fields_set.symmetric_difference(['a', 'b'])
    assert type(result) is ModelFieldsSet
    assert result == {'b', 'c', 'x'}
    assert fields_set == {'a', 'c', 'x'}


def test_issubset_issuperset_isdisjoint(fields_set: ModelFieldsSet) -> None:
    assert fields_set.issubset(['a', 'c', 'x', 'y'])
    assert fields_set.issubset(fields_set)
    assert not fields_set.issubset(['a'])
    assert fields_set.issuperset(['a', 'c'])
    assert fields_set.issuperset(fields_set)
    assert not fields_set.issuperset(['a', 'b'])
    assert fields_set.isdisjoint(['b', 1])
    assert not fields_set.isdisjoint(['a'])
    assert not fields_set.isdisjoint(fields_set)


def test_binary_operators(fields_set: ModelFieldsSet) -> None:
    for result in (fields_set | {'b'}, fields_set | frozenset({'b'}), fields_set | {'b': 1}.keys()):
        assert type(result) is ModelFieldsSet
        assert result == {'a', 'b', 'c', 'x'}
    assert fields_set | fields_set == fields_set

    assert fields_set & {'a', 'b'} == {'a'}
    assert type(fields_set & {'a', 'b'}) is ModelFieldsSet
    assert fields_set - {'a', 'b'} == {'c', 'x'}
    assert type(fields_set - {'a', 'b'}) is ModelFieldsSet
    assert fields_set ^ {'a', 'b'} == {'b', 'c', 'x'}
    assert type(fields_set ^ {'a', 'b'}) is ModelFieldsSet

    assert fields_set == {'a', 'c', 'x'}

    for other in (['a'], 'a', 1, None):
        with pytest.raises(TypeError):
            fields_set | other
        with pytest.raises(TypeError):
            fields_set & other
        with pytest.raises(TypeError):
            fields_set - other
        with pytest.raises(TypeError):
            fields_set ^ other


def test_reflected_binary_operators(fields_set: ModelFieldsSet) -> None:
    result = {'b'} | fields_set
    assert type(result) is set
    assert result == {'a', 'b', 'c', 'x'}
    result = frozenset({'b'}) | fields_set
    assert type(result) is frozenset
    assert result == {'a', 'b', 'c', 'x'}
    result = {'b': 1}.keys() | fields_set
    assert result == {'a', 'b', 'c', 'x'}

    assert {'a', 'b'} & fields_set == {'a'}
    assert type({'a', 'b'} & fields_set) is set
    assert {'a', 'b'} - fields_set == {'b'}
    assert type({'a', 'b'} - fields_set) is set
    assert {'a', 'b'} ^ fields_set == {'b', 'c', 'x'}
    assert type({'a', 'b'} ^ fields_set) is set
    assert type(frozenset({'a', 'b'}) ^ fields_set) is frozenset

    for other in (['a'], 'a', 1, None):
        with pytest.raises(TypeError):
            other | fields_set
        with pytest.raises(TypeError):
            other & fields_set
        with pytest.raises(TypeError):
            other - fields_set
        with pytest.raises(TypeError):
            other ^ fields_set


def test_inplace_operators(fields_set: ModelFieldsSet) -> None:
    original = fields_set
    fields_set |= {'b'}
    assert fields_set is original
    assert fields_set == {'a', 'b', 'c', 'x'}
    fields_set |= {'y': 1}.keys()
    assert fields_set == {'a', 'b', 'c', 'x', 'y'}
    fields_set -= {'y'}
    assert fields_set is original
    assert fields_set == {'a', 'b', 'c', 'x'}
    fields_set &= {'a', 'x', 'unknown'}
    assert fields_set is original
    assert fields_set == {'a', 'x'}
    fields_set ^= {'a', 'b'}
    assert fields_set is original
    assert fields_set == {'b', 'x'}

    fields_set |= fields_set
    assert fields_set == {'b', 'x'}
    fields_set &= fields_set
    assert fields_set == {'b', 'x'}
    fields_set ^= fields_set
    assert fields_set == set()
    fields_set |= {'a'}
    fields_set -= fields_set
    assert fields_set == set()

    for other in (['a'], 'a', 1, None):
        with pytest.raises(TypeError):
            fields_set |= other
        with pytest.raises(TypeError):
            fields_set &= other
        with pytest.raises(TypeError):
            fields_set -= other
        with pytest.raises(TypeError):
            fields_set ^= other


@pytest.mark.parametrize(
    ['method', 'expected'],
    [
        ('update', {'a', 'b', 'c', 'x', 'y'}),
        ('difference_update', {'a', 'c', 'x', 'y'}),
        ('intersection_update', set()),
        ('symmetric_difference_update', {'a', 'b', 'c', 'x', 'y'}),
    ],
)
def test_update_from_reentrant_iterable(fields_set: ModelFieldsSet, method: str, expected: set[str]) -> None:
    """Like `set`, the iterable passed to a mutating method can call back into the set while being consumed."""

    def gen():
        fields_set.add('y')
        yield 'b'

    getattr(fields_set, method)(gen())
    assert fields_set == expected
    # The same holds for a plain set:
    plain = {'a', 'c', 'x'}

    def plain_gen():
        plain.add('y')
        yield 'b'

    getattr(plain, method)(plain_gen())
    assert plain == expected


def test_iteration_snapshot(fields_set: ModelFieldsSet) -> None:
    iterator = iter(fields_set)
    assert next(iterator) == 'a'
    fields_set.discard('c')
    fields_set.add('b')
    # Known fields are iterated over from a snapshot:
    assert next(iterator) == 'c'
    assert next(iterator) == 'x'
    with pytest.raises(StopIteration):
        next(iterator)


def test_serialization_exclude_unset() -> None:
    v = make_validator('allow')
    s = SchemaSerializer(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.int_schema()),
                    'b': core_schema.model_field(core_schema.int_schema()),
                    'c': core_schema.model_field(core_schema.int_schema()),
                },
                extra_behavior='allow',
            ),
            extra_behavior='allow',
        )
    )
    m = v.validate_python({'a': 1, 'c_alias': 3, 'x': 10})
    assert s.to_python(m) == {'a': 1, 'b': 2, 'c': 3, 'x': 10}
    assert s.to_python(m, exclude_unset=True) == {'a': 1, 'c': 3, 'x': 10}
    assert s.to_json(m, exclude_unset=True) == b'{"a":1,"c":3,"x":10}'

    m.__pydantic_fields_set__.discard('c')
    assert s.to_python(m, exclude_unset=True) == {'a': 1, 'x': 10}

    # A plain set is supported as well:
    m.__pydantic_fields_set__ = {'b'}
    assert s.to_python(m, exclude_unset=True) == {'b': 2, 'x': 10}
    assert s.to_json(m, exclude_unset=True) == b'{"b":2,"x":10}'

    m.__pydantic_fields_set__ = ['a']
    with pytest.raises(TypeError, match='must be a `ModelFieldsSet` or `set` instance, got list'):
        s.to_python(m, exclude_unset=True)


@pytest.mark.parametrize('use_plain_set', [False, True])
def test_validate_assignment(use_plain_set: bool) -> None:
    v = make_validator('allow')
    m = v.validate_python({'a': 1})
    if use_plain_set:
        m.__pydantic_fields_set__ = set(m.__pydantic_fields_set__)
    fields_set = m.__pydantic_fields_set__

    v.validate_assignment(m, 'b', 4)
    assert m.__pydantic_fields_set__ is fields_set
    assert m.__pydantic_fields_set__ == {'a', 'b'}
    v.validate_assignment(m, 'y', 4)
    assert m.__pydantic_fields_set__ == {'a', 'b', 'y'}
    assert m.__pydantic_extra__ == {'y': 4}


def test_validate_assignment_unsupported_fields_set() -> None:
    """Only `ModelFieldsSet` and `set` are supported as `__pydantic_fields_set__`."""
    v = make_validator()
    m = v.validate_python({'a': 1})
    m.__pydantic_fields_set__ = ['a']
    with pytest.raises(TypeError, match='must be a `ModelFieldsSet` or `set` instance, got list'):
        v.validate_assignment(m, 'b', 4)


def test_revalidation_reuses_fields_set() -> None:
    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            revalidate_instances='always',
        )
    )
    m = v.validate_python({'a': 1})
    m.__pydantic_fields_set__ = {'a', 'custom'}
    m2 = v.validate_python(m)
    assert m2 is not m
    assert m2.__pydantic_fields_set__ is m.__pydantic_fields_set__


def test_v1_style_wrap_validator_replacing_fields_set() -> None:
    """The fields set can be replaced by a plain `set` in a wrap validator around the fields."""

    def wrap(value: Any, handler: Any) -> Any:
        model_dict, model_extra, _ = handler(value)
        return model_dict, model_extra, {'replaced'}

    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.no_info_wrap_validator_function(
                wrap,
                core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            ),
        )
    )
    m = v.validate_python({'a': 1})
    assert m.__pydantic_fields_set__ == {'replaced'}
    assert type(m.__pydantic_fields_set__) is set


def test_many_fields() -> None:
    """More than 64 fields, requiring more than one bitset block."""
    n = 150
    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {
                    f'f{i}': core_schema.model_field(
                        core_schema.with_default_schema(core_schema.int_schema(), default=0)
                    )
                    for i in range(n)
                }
            ),
        )
    )
    m = v.validate_python({'f0': 1, 'f63': 1, 'f64': 1, 'f149': 1})
    assert m.__pydantic_fields_set__ == {'f0', 'f63', 'f64', 'f149'}
    assert list(m.__pydantic_fields_set__) == ['f0', 'f63', 'f64', 'f149']
    assert 'f1' not in m.__pydantic_fields_set__
    assert 'f128' not in m.__pydantic_fields_set__
    m.__pydantic_fields_set__.update(f'f{i}' for i in range(n))
    assert len(m.__pydantic_fields_set__) == n
    assert list(m.__pydantic_fields_set__) == [f'f{i}' for i in range(n)]
    m.__pydantic_fields_set__.discard('f64')
    assert len(m.__pydantic_fields_set__) == n - 1
    assert m.__pydantic_fields_set__.pop() == 'f0'
