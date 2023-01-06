from pydantic import BaseConfig, BaseModel, ValidationError


class Model(BaseModel):
    model_config = BaseConfig(str_max_length=10)
    v: str


try:
    m = Model(v='x' * 20)
except ValidationError as e:
    print(e)
