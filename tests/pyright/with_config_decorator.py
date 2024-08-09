from typing import TypedDict

from typing_extensions import assert_type

from pydantic import ConfigDict, with_config


@with_config(ConfigDict(str_to_lower=True))
class Model(TypedDict):
    a: str


assert_type(Model, type[Model])

model = Model(a='ABC')

assert_type(model, Model)
