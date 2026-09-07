from collections.abc import Mapping

import pytest

from pydantic_core import ArgsKwargs, SchemaValidator, ValidationError, core_schema


@pytest.mark.parametrize(
    'schema',
    [
        core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(core_schema.int_schema())}),
        core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
        core_schema.arguments_v3_schema([core_schema.arguments_v3_parameter('a', core_schema.int_schema())]),
    ],
    ids=['typed-dict', 'model-fields', 'arguments-v3'],
)
def test_ignored_mapping_extras_are_not_enumerated(schema):
    calls = []

    class Input(Mapping):
        def __getitem__(self, key):
            calls.append(key)
            if key == 'a':
                return 1
            raise KeyError(key)

        def __iter__(self):
            raise AssertionError('Input should not be iterated')

        def __len__(self):
            raise AssertionError('Input length should not be requested')

    validator = SchemaValidator(schema)
    result = validator.validate_python(Input(), extra='ignore')
    assert calls == ['a']
    assert result == validator.validate_json('{"a": 1}', extra='ignore')


@pytest.mark.parametrize('extra_behavior', ['ignore', 'allow', 'forbid'])
def test_attribute_extras_are_not_enumerated(extra_behavior):
    class Input:
        a = 1

        def __dir__(self):
            raise AssertionError('Attributes should not be enumerated')

    validator = SchemaValidator(
        core_schema.model_fields_schema(
            {'a': core_schema.model_field(core_schema.int_schema())},
            from_attributes=True,
            extra_behavior=extra_behavior,
        )
    )
    assert validator.validate_python(Input()) == ({'a': 1}, {} if extra_behavior == 'allow' else None, {'a'})


@pytest.mark.parametrize(
    'schema',
    [
        core_schema.arguments_schema([core_schema.arguments_parameter('a', core_schema.int_schema())]),
        core_schema.arguments_v3_schema(
            [core_schema.arguments_v3_parameter('a', core_schema.int_schema())], extra_behavior='ignore'
        ),
        core_schema.dataclass_args_schema(
            'Result', [core_schema.dataclass_field('a', core_schema.int_schema())], extra_behavior='ignore'
        ),
    ],
    ids=['arguments', 'arguments-v3', 'dataclass-args'],
)
def test_ignored_kwargs_still_validate_keys(schema):
    validator = SchemaValidator(schema, config=core_schema.CoreConfig(extra_fields_behavior='ignore'))
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python(ArgsKwargs((), {'a': 1, 2: 3}))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'invalid_key', 'loc': (2,), 'msg': 'Keys should be strings', 'input': 2}
    ]


def test_var_kwargs_are_collected_when_extras_ignored():
    validator = SchemaValidator(
        core_schema.arguments_schema(
            [core_schema.arguments_parameter('a', core_schema.int_schema())],
            var_kwargs_schema=core_schema.int_schema(),
        ),
        config=core_schema.CoreConfig(extra_fields_behavior='ignore'),
    )
    assert validator.validate_json('{"a": 1, "extra": "2"}') == ((), {'a': 1, 'extra': 2})
