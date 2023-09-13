from pydantic_core import PydanticUndefined

from pydantic import create_model

Model = create_model('Model', value=(str, PydanticUndefined))


m = Model(value='abc')
