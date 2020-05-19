import itertools
from typing import Iterable
from pydantic import BaseModel, validator, ValidationError
from pydantic.fields import ModelField


class Model(BaseModel):
    infinite: Iterable[int]

    @validator('infinite')
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def infinite_first_int(cls, iterable, field: ModelField):
        first_value = next(iterable)
        if field.sub_fields:
            # The Iterable had a parameter type, in this case it's int
            # We use it to validate the first value
            sub_field = field.sub_fields[0]
            v, error = sub_field.validate(first_value, {}, loc='first_value')
            if error:
                raise ValidationError([error], cls)
        # This creates a new generator that returns the first value and then
        # the rest of the values from the (already started) iterable
        return itertools.chain([first_value], iterable)


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)


def infinite_strs():
    while True:
        for letter in 'allthesingleladies':
            yield letter


try:
    Model(infinite=infinite_strs())
except ValidationError as e:
    print(e)
