from pydantic_core import SchemaValidator


def test_simple():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int'}}})

    assert v.run({'field_a': 123, 'field_b': 1}) == {
        'fields_set': {'field_b', 'field_a'},
        'values': {'field_a': '123', 'field_b': 1},
    }
