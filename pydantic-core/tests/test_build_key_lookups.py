"""Schema / config key lookups while building validators must behave exactly like plain `dict` lookups, whatever
bookkeeping is used internally to skip lookups of keys that can't be present (`SchemaKeys` / `BuildConfig`)."""

import pytest
from pydantic_core import SchemaError, SchemaValidator, ValidationError


def non_interned(s: str) -> str:
    # an equal but distinct str object (not the interned constant)
    return ''.join(list(s))


class Str(str):
    __slots__ = ()


class LyingStr(str):
    """A str subclass whose equality claims to match a different key."""

    __slots__ = ()

    def __eq__(self, other):
        return other == 'max_length' or str.__eq__(self, other)

    def __hash__(self):
        return hash('max_length')


def test_str_constraints_with_non_interned_keys():
    schema = {non_interned('type'): non_interned('str'), non_interned('max_length'): 3, non_interned('to_upper'): True}
    v = SchemaValidator(schema)
    assert v.validate_python('abc') == 'ABC'
    with pytest.raises(ValidationError):
        v.validate_python('abcd')


def test_str_constraints_with_str_subclass_keys():
    v = SchemaValidator({Str('type'): 'str', Str('min_length'): 2})
    with pytest.raises(ValidationError):
        v.validate_python('a')
    assert v.validate_python('ab') == 'ab'


def test_key_with_custom_eq_is_honoured_like_dict_lookup():
    schema = {'type': 'str', LyingStr('whatever'): 2}
    # plain dict semantics: the lying key answers for 'max_length'
    assert schema.get('max_length') == 2
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError):
        v.validate_python('abc')


def test_config_str_settings_with_non_interned_and_subclass_keys():
    v = SchemaValidator({'type': 'str'}, {non_interned('str_max_length'): 2})
    with pytest.raises(ValidationError):
        v.validate_python('abc')
    v = SchemaValidator({'type': 'str'}, {Str('str_to_lower'): True})
    assert v.validate_python('ABC') == 'abc'
    v = SchemaValidator({'type': 'str'}, {LyingStr('x'): 5, 'str_max_length': 1})
    # 'str_max_length' is looked up; whichever entry the dict returns for it wins, as for a plain lookup
    expected = {LyingStr('x'): 5, 'str_max_length': 1}.get('str_max_length')
    assert v.validate_python('a' * expected) == 'a' * expected
    with pytest.raises(ValidationError):
        v.validate_python('a' * (expected + 1))


def test_config_with_non_str_key():
    # a non-str key in the config must not confuse the lookups of real keys
    v = SchemaValidator({'type': 'str'}, {1: 2, 'str_max_length': 2})
    with pytest.raises(ValidationError):
        v.validate_python('abc')
    v = SchemaValidator({'type': 'int'}, {(1, 2): 'x', 'strict': True})
    with pytest.raises(ValidationError):
        v.validate_python('1')


def test_same_config_dict_shared_by_nested_models():
    class M:
        __slots__ = ('__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__')

    config = {'str_max_length': 1, 'strict': True}
    inner = {
        'type': 'model',
        'cls': M,
        'config': config,
        'schema': {'type': 'model-fields', 'fields': {'a': {'type': 'model-field', 'schema': {'type': 'str'}}}},
    }
    outer = {
        'type': 'model',
        'cls': M,
        'config': config,
        'schema': {
            'type': 'model-fields',
            'fields': {
                'b': {'type': 'model-field', 'schema': {'type': 'str'}},
                'm': {'type': 'model-field', 'schema': inner},
            },
        },
    }
    v = SchemaValidator(outer, config)
    assert v.validate_python({'b': 'x', 'm': {'a': 'y'}}).m.a == 'y'
    with pytest.raises(ValidationError):
        v.validate_python({'b': 'x', 'm': {'a': 'yy'}})
    with pytest.raises(ValidationError):
        v.validate_python({'b': 'xx', 'm': {'a': 'y'}})


def test_default_schema_key_order_of_errors_unchanged():
    # both problems present: the default/default_factory clash is still reported (before the missing 'schema')
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator({'type': 'default', 'default': 1, 'default_factory': int})
    with pytest.raises(SchemaError, match='KeyError'):
        SchemaValidator({'type': 'default', 'default': 1})


def test_default_with_extra_keys_still_reads_options():
    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'default': 1, 'on_error': 'default', 'metadata': {}, 'ref': 'r'}
    )
    assert v.validate_python('x') == 1


def test_model_fields_optional_keys_with_and_without_extras():
    v = SchemaValidator(
        {
            'type': 'model-fields',
            'fields': {'a': {'type': 'model-field', 'schema': {'type': 'int'}}},
            'model_name': 'X',
            'computed_fields': [],
        }
    )
    assert v.validate_python({'a': '1'})[0] == {'a': 1}
    v = SchemaValidator(
        {
            'type': 'model-fields',
            'fields': {'a': {'type': 'model-field', 'schema': {'type': 'int'}}},
            'model_name': 'X',
            'computed_fields': [],
            'from_attributes': True,
            'extra_behavior': 'forbid',
        }
    )
    with pytest.raises(ValidationError):
        v.validate_python({'a': 1, 'b': 2})

    class Obj:
        a = 3

    assert v.validate_python(Obj())[0] == {'a': 3}


@pytest.mark.parametrize('extra_key', [None, 'metadata', 'serialization'])
def test_list_and_dict_constraints(extra_key):
    extra = {} if extra_key is None else {extra_key: {}}
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'max_length': 1, **extra})
    with pytest.raises(ValidationError):
        v.validate_python([1, 2])
    v = SchemaValidator(
        {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}, 'min_length': 1, **extra}
    )
    with pytest.raises(ValidationError):
        v.validate_python({})
    v = SchemaValidator({'type': 'int', **extra}, {'strict': True})
    with pytest.raises(ValidationError):
        v.validate_python('1')
