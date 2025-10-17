from pydantic_core import SchemaSerializer, core_schema


def test_json_int():
    s = SchemaSerializer(core_schema.json_schema(core_schema.int_schema()))

    assert s.to_python(1) == 1
    assert s.to_python(1, round_trip=True) == '1'
    assert s.to_python(1, mode='json') == 1
    assert s.to_python(1, mode='json', round_trip=True) == '1'
    assert s.to_json(1) == b'1'
    assert s.to_json(1, round_trip=True) == b'"1"'


def test_list_json():
    s = SchemaSerializer(core_schema.list_schema(core_schema.json_schema()))

    v = ['a', [1, 2], None]
    assert s.to_python(v) == v
    assert s.to_python(v, round_trip=True) == ['"a"', '[1,2]', 'null']
    assert s.to_python(v, mode='json') == v
    assert s.to_python(v, mode='json', round_trip=True) == ['"a"', '[1,2]', 'null']
    assert s.to_json(v) == b'["a",[1,2],null]'
    assert s.to_json(v, round_trip=True) == b'["\\"a\\"","[1,2]","null"]'


def test_dict_key_json():
    s = SchemaSerializer(core_schema.dict_schema(core_schema.json_schema(), core_schema.any_schema()))

    v = {(1, 2): 3, (4, 5): 9}
    assert s.to_python(v) == v
    assert s.to_python(v, round_trip=True) == {'[1,2]': 3, '[4,5]': 9}

    assert s.to_python(v, mode='json') == {'1,2': 3, '4,5': 9}
    assert s.to_python(v, mode='json', round_trip=True) == {'[1,2]': 3, '[4,5]': 9}

    assert s.to_json(v) == b'{"1,2":3,"4,5":9}'
    assert s.to_json(v, round_trip=True) == b'{"[1,2]":3,"[4,5]":9}'


def test_custom_serializer():
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.simple_ser_schema('json')))
    assert s.to_python({1: 2}) == {1: 2}
    assert s.to_python({1: 2}, mode='json') == {'1': 2}
    assert s.to_python({1: 2}, mode='json', round_trip=True) == '{"1":2}'
    assert s.to_json({1: 2}) == b'{"1":2}'
    assert s.to_json({1: 2}, round_trip=True) == b'"{\\"1\\":2}"'
