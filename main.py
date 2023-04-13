from pydantic import BaseModel
from pydantic.config import Extra
from pydantic.deprecated import tools
from pydantic.deprecated.config import BaseConfig
from pydantic.deprecated.decorator import validate_arguments
from pydantic.deprecated.tools import schema_json_of, schema_of


class MyModel(BaseModel):
    potato: str

print(tools.schema_of(MyModel, title=lambda x: "haha"))
print(tools.schema_json_of(MyModel))


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def foo(potato: str):
    pass

foo(potato="1")

Extra.allow
getattr(Extra, "allow")
getattr(Extra, "allow")
