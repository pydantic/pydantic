import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs


def test_json_or_python():
    class Foo(str):
        def __eq__(self, o: object) -> bool:
            if isinstance(o, Foo) and super().__eq__(o):
                return True
            return False

    s = cs.json_or_python_schema(
        json_schema=cs.no_info_after_validator_function(Foo, cs.str_schema()), python_schema=cs.is_instance_schema(Foo)
    )
    v = SchemaValidator(s)

    assert v.validate_python(Foo('abc')) == Foo('abc')
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('abc')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (),
            'msg': 'Input should be an instance of test_json_or_python.<locals>.Foo',
            'input': 'abc',
            'ctx': {'class': 'test_json_or_python.<locals>.Foo'},
        }
    ]

    assert v.validate_json('"abc"') == Foo('abc')
