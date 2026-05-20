from typing import Any

from typing_extensions import Self

from pydantic import BaseModel, create_model


class Model(BaseModel):
    a: int


SubModel = create_model('SubModel', __base__=Model)


class Main(BaseModel):
    sub: SubModel


DynamicFieldsModel = create_model(
    'DynamicFieldsModel',
    __base__=Model,
    __module__=Model.__module__,
    parameter_1=(int, ...),
    parameter_2=(str, None),
)

dynamic_fields_model = DynamicFieldsModel(a=1, parameter_1=1)
dynamic_parameter_1: int = dynamic_fields_model.parameter_1
dynamic_a: int = dynamic_fields_model.a

LiteralKwargsModel = create_model('LiteralKwargsModel', **{'literal_parameter': (int, ...)})
literal_kwargs_model = LiteralKwargsModel(literal_parameter=1)
literal_parameter: int = literal_kwargs_model.literal_parameter

field_definitions = {'dict_parameter': (str, ...)}
DictKwargsModel = create_model('DictKwargsModel', **field_definitions)
dict_kwargs_model = DictKwargsModel(dict_parameter='value')
dict_parameter: str = dict_kwargs_model.dict_parameter

SpecialKwargsModel = create_model('SpecialKwargsModel', **{'__base__': Model, 'special_parameter': (int, ...)})
special_kwargs_model = SpecialKwargsModel(a=1, special_parameter=2)
special_a: int = special_kwargs_model.a
special_parameter: int = special_kwargs_model.special_parameter


# This only crashes in parallel mode (see https://github.com/python/mypy/issues/21472):
def dyn_model() -> type[BaseModel]:
    local_field_definitions = {'local_parameter': (int, ...)}
    LocalKwargsModel = create_model('LocalKwargsModel', **local_field_definitions)
    local_kwargs_model = LocalKwargsModel(local_parameter=1)
    local_parameter: int = local_kwargs_model.local_parameter

    Inner = create_model("Inner", __base__=BaseModel, value=(int, ...))

    class Outer(Inner):
        pass

    return Outer


class ClassmethodModel(BaseModel):
    @classmethod
    def composite(cls) -> type[Self]:
        # Ensures the mypy plugin defers to the `create_model()` overload:
        model = create_model(cls.__name__, __base__=cls)
        return model
