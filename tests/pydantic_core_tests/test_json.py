import platform

import pydantic_core
import pytest
from dirty_equals import IsList
from pydantic_core import (
    CoreConfig,
    PydanticSerializationError,
    SchemaSerializer,
    SchemaValidator,
    ValidationError,
    core_schema,
    from_json,
    to_json,
    to_jsonable_python,
)


class Foobar:
    def __str__(self):
        return 'Foobar.__str__'


def fallback_func(v):
    return f'fallback:{type(v).__name__}'


def test_to_json():
    assert to_json([1, 2]) == b'[1,2]'
    assert to_json([1, 2], indent=2) == b'[\n  1,\n  2\n]'
    assert to_json([1, b'x']) == b'[1,"x"]'
    assert to_json(['à', 'é']).decode('utf-8') == '["à","é"]'
    assert to_json(['à', 'é'], indent=2).decode('utf-8') == '[\n  "à",\n  "é"\n]'
    assert to_json(['à', 'é'], indent=2, ensure_ascii=True).decode('utf-8') == '[\n  "\\u00e0",\n  "\\u00e9"\n]'

    # kwargs required
    with pytest.raises(TypeError, match=r'to_json\(\) takes 1 positional arguments but 2 were given'):
        to_json([1, 2], 2)


def test_to_json_fallback():
    with pytest.raises(PydanticSerializationError, match=r'Unable to serialize unknown type: <.+\.Foobar'):
        to_json(Foobar())

    assert to_json(Foobar(), serialize_unknown=True) == b'"Foobar.__str__"'
    assert to_json(Foobar(), serialize_unknown=True, fallback=fallback_func) == b'"fallback:Foobar"'
    assert to_json(Foobar(), fallback=fallback_func) == b'"fallback:Foobar"'


def test_to_jsonable_python():
    assert to_jsonable_python([1, 2]) == [1, 2]
    assert to_jsonable_python({1, 2}) == IsList(1, 2, check_order=False)
    assert to_jsonable_python([1, b'x']) == [1, 'x']
    assert to_jsonable_python([0, 1, 2, 3, 4], exclude={1, 3}) == [0, 2, 4]


def test_to_jsonable_python_fallback():
    with pytest.raises(PydanticSerializationError, match=r'Unable to serialize unknown type: <.+\.Foobar'):
        to_jsonable_python(Foobar())

    assert to_jsonable_python(Foobar(), serialize_unknown=True) == 'Foobar.__str__'
    assert to_jsonable_python(Foobar(), serialize_unknown=True, fallback=fallback_func) == 'fallback:Foobar'
    assert to_jsonable_python(Foobar(), fallback=fallback_func) == 'fallback:Foobar'


def test_to_jsonable_python_schema_serializer():
    class Foobar:
        def __init__(self, my_foo: int, my_inners: list['Foobar']):
            self.my_foo = my_foo
            self.my_inners = my_inners

    # force a recursive model to ensure we exercise the transfer of definitions from the loaded
    # serializer
    c = core_schema.definitions_schema(
        core_schema.definition_reference_schema(schema_ref='foobar'),
        [
            core_schema.model_schema(
                Foobar,
                core_schema.typed_dict_schema(
                    {
                        'my_foo': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='myFoo'),
                        'my_inners': core_schema.typed_dict_field(
                            core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
                            serialization_alias='myInners',
                        ),
                    }
                ),
                ref='foobar',
            )
        ],
    )
    v = SchemaValidator(c)
    s = SchemaSerializer(c)

    Foobar.__pydantic_validator__ = v
    Foobar.__pydantic_serializer__ = s

    instance = Foobar(my_foo=1, my_inners=[Foobar(my_foo=2, my_inners=[])])
    assert to_jsonable_python(instance, by_alias=True) == {'myFoo': 1, 'myInners': [{'myFoo': 2, 'myInners': []}]}
    assert to_jsonable_python(instance, by_alias=False) == {'my_foo': 1, 'my_inners': [{'my_foo': 2, 'my_inners': []}]}
    assert to_json(instance, by_alias=True) == b'{"myFoo":1,"myInners":[{"myFoo":2,"myInners":[]}]}'
    assert to_json(instance, by_alias=False) == b'{"my_foo":1,"my_inners":[{"my_foo":2,"my_inners":[]}]}'


def test_cycle_same():
    def fallback_func_passthrough(obj):
        return obj

    f = Foobar()

    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        to_jsonable_python(f, fallback=fallback_func_passthrough)

    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        to_json(f, fallback=fallback_func_passthrough)


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy' and pydantic_core._pydantic_core.build_profile == 'debug',
    reason='PyPy does not have enough stack space for Rust debug builds to recurse very deep',
)
def test_cycle_change():
    def fallback_func_change_id(obj):
        return Foobar()

    f = Foobar()

    with pytest.raises(ValueError, match=r'Circular reference detected \(depth exceeded\)'):
        to_jsonable_python(f, fallback=fallback_func_change_id)

    with pytest.raises(ValueError, match=r'Circular reference detected \(depth exceeded\)'):
        to_json(f, fallback=fallback_func_change_id)


class FoobarHash:
    def __str__(self):
        return 'Foobar.__str__'

    def __hash__(self):
        return 1


def test_json_key_fallback():
    x = {FoobarHash(): 1}

    assert to_jsonable_python(x, serialize_unknown=True) == {'Foobar.__str__': 1}
    assert to_jsonable_python(x, fallback=fallback_func) == {'fallback:FoobarHash': 1}
    assert to_json(x, serialize_unknown=True) == b'{"Foobar.__str__":1}'
    assert to_json(x, fallback=fallback_func) == b'{"fallback:FoobarHash":1}'


class BedReprMeta(type):
    def __repr__(self):
        raise ValueError('bad repr')


class BadRepr(metaclass=BedReprMeta):
    def __repr__(self):
        raise ValueError('bad repr')

    def __hash__(self):
        return 1


def test_bad_repr():
    b = BadRepr()

    error_msg = '^Unable to serialize unknown type: <unprintable BedReprMeta object>$'
    with pytest.raises(PydanticSerializationError, match=error_msg):
        to_jsonable_python(b)

    assert to_jsonable_python(b, serialize_unknown=True) == '<Unserializable BadRepr object>'

    with pytest.raises(PydanticSerializationError, match=error_msg):
        to_json(b)

    assert to_json(b, serialize_unknown=True) == b'"<Unserializable BadRepr object>"'


def test_partial_parse():
    with pytest.raises(ValueError, match='EOF while parsing a string at line 1 column 15'):
        from_json('["aa", "bb", "c')
    assert from_json('["aa", "bb", "c', allow_partial=True) == ['aa', 'bb']

    with pytest.raises(ValueError, match='EOF while parsing a string at line 1 column 15'):
        from_json(b'["aa", "bb", "c')
    assert from_json(b'["aa", "bb", "c', allow_partial=True) == ['aa', 'bb']


def test_json_bytes_base64_round_trip():
    data = b'\xd8\x07\xc1Tx$\x91F%\xf3\xf3I\xca\xd8@\x0c\xee\xc3\xab\xff\x7f\xd3\xcd\xcd\xf9\xc2\x10\xe4\xa1\xb01e'
    encoded_std = b'"2AfBVHgkkUYl8/NJythADO7Dq/9/083N+cIQ5KGwMWU="'
    encoded_url = b'"2AfBVHgkkUYl8_NJythADO7Dq_9_083N-cIQ5KGwMWU="'
    assert to_json(data, bytes_mode='base64') == encoded_url

    v = SchemaValidator(core_schema.bytes_schema(), config=CoreConfig(val_json_bytes='base64'))
    assert v.validate_json(encoded_url) == data
    assert v.validate_json(encoded_std) == data

    with pytest.raises(ValidationError) as exc:
        v.validate_json('"wrong!"')
    [details] = exc.value.errors()
    assert details['type'] == 'bytes_invalid_encoding'

    assert to_json({'key': data}, bytes_mode='base64') == b'{"key":' + encoded_url + b'}'
    v = SchemaValidator(
        core_schema.dict_schema(keys_schema=core_schema.str_schema(), values_schema=core_schema.bytes_schema()),
        config=CoreConfig(val_json_bytes='base64'),
    )
    assert v.validate_json(b'{"key":' + encoded_url + b'}') == {'key': data}


def test_json_bytes_base64_no_padding():
    v = SchemaValidator(core_schema.bytes_schema(), config=CoreConfig(val_json_bytes='base64'))
    base_64_without_padding = 'bm8tcGFkZGluZw'
    assert v.validate_json(f'"{base_64_without_padding}"') == b'no-padding'


def test_json_bytes_base64_invalid():
    v = SchemaValidator(core_schema.bytes_schema(), config=CoreConfig(val_json_bytes='base64'))
    wrong_input = 'wrong!'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json(f'"{wrong_input}"')
    assert exc_info.value.errors(include_url=False, include_context=False) == [
        {
            'type': 'bytes_invalid_encoding',
            'loc': (),
            'msg': f'Data should be valid base64: Invalid symbol {ord("!")}, offset {len(wrong_input) - 1}.',
            'input': wrong_input,
        }
    ]


def test_json_bytes_hex_round_trip():
    data = b'hello'
    encoded = b'"68656c6c6f"'
    assert to_json(data, bytes_mode='hex') == encoded

    v = SchemaValidator(core_schema.bytes_schema(), config=CoreConfig(val_json_bytes='hex'))
    assert v.validate_json(encoded) == data

    assert to_json({'key': data}, bytes_mode='hex') == b'{"key":"68656c6c6f"}'
    v = SchemaValidator(
        core_schema.dict_schema(keys_schema=core_schema.str_schema(), values_schema=core_schema.bytes_schema()),
        config=CoreConfig(val_json_bytes='hex'),
    )
    assert v.validate_json('{"key":"68656c6c6f"}') == {'key': data}


def test_json_bytes_hex_invalid():
    v = SchemaValidator(core_schema.bytes_schema(), config=CoreConfig(val_json_bytes='hex'))

    wrong_input = 'a'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json(f'"{wrong_input}"')
    assert exc_info.value.errors(include_url=False, include_context=False) == [
        {
            'type': 'bytes_invalid_encoding',
            'loc': (),
            'msg': 'Data should be valid hex: Odd number of digits',
            'input': wrong_input,
        }
    ]

    wrong_input = 'ag'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json(f'"{wrong_input}"')
    assert exc_info.value.errors(include_url=False, include_context=False) == [
        {
            'type': 'bytes_invalid_encoding',
            'loc': (),
            'msg': "Data should be valid hex: Invalid character 'g' at position 1",
            'input': wrong_input,
        }
    ]
