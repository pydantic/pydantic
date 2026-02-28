import dataclasses

from pydantic import BaseModel, field_serializer

from pydantic_core import ReturnAsIs


@dataclasses.dataclass
class Foo:
    a: str
    b: int


def test_return_as_is_return_data_class():
    @dataclasses.dataclass
    class Foo:
        a: int
        b: str

    class Bar(BaseModel):
        foo: Foo

        @field_serializer('foo', return_type=ReturnAsIs)
        def ser_foo(self, value):
            return self.foo

    foo = Foo(a=1729, b='foo')
    bar = Bar(foo=foo)
    assert bar.model_dump() == {'foo': foo}
    assert bar.model_dump_json() == '{"foo":{"a":1729,"b":"foo"}}'
