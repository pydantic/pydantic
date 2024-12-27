from typing import Any

from pydantic_core import PydanticUndefined

from pydantic import BaseModel, Field, ModelFieldDescriptor


class FieldDescriptor(ModelFieldDescriptor):
    def __init__(self, /, default: Any = PydanticUndefined, field=None):
        super().__init__(default=default, field=field)
        self.__values = {}

    def __get__(self, instance, owner):
        if instance is not None:
            try:
                return self.__values[id(instance)][self.name]
            except KeyError:
                return self.field.default

        return self

    def __set__(self, instance, value):
        self.__values.setdefault(id(instance), {})[self.name] = value


def test_descriptor_fields():
    class DescriptorAndRegularFields(BaseModel):
        my_str: str = FieldDescriptor(field=Field('string_value', alias='myStr'))
        my_int: int

    assert DescriptorAndRegularFields.__pydantic_descriptor_fields__ == {'my_str'}

    # The below to be enabled once corresponding pydantic-core change released

    # instance = DescriptorAndRegularFields(my_int=123)
    #
    # assert instance.my_str == "string_value"
    # assert instance.my_int == 123
    #
    # instance.my_int = 321
    # assert instance.my_int == 321
    #
    # instance.my_str = "new string value"
    # assert instance.my_str == "new string value"
    #
    # assert "my_str" not in instance.__dict__
    # assert "my_int" in instance.__dict__
    #
    # assert instance.model_dump() == {"my_str": "new string value", "my_int": 321}
