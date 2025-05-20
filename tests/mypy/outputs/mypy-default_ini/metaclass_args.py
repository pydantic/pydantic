from pydantic import BaseModel, Field


class ConfigClassUsed(BaseModel):
    i: int = Field(2, alias='j')

    class Config:
        validate_by_name = True


ConfigClassUsed(i=None)
# MYPY: error: Unexpected keyword argument "i" for "ConfigClassUsed"  [call-arg]


class MetaclassArgumentsNoDefault(BaseModel, validate_by_name=True):
    i: int = Field(alias='j')


MetaclassArgumentsNoDefault(i=None)
# MYPY: error: Unexpected keyword argument "i" for "MetaclassArgumentsNoDefault"  [call-arg]


class MetaclassArgumentsWithDefault(BaseModel, validate_by_name=True):
    i: int = Field(2, alias='j')


MetaclassArgumentsWithDefault(i=None)
# MYPY: error: Unexpected keyword argument "i" for "MetaclassArgumentsWithDefault"  [call-arg]


class NoArguments(BaseModel):
    i: int = Field(2, alias='j')


NoArguments(i=1)
# MYPY: error: Unexpected keyword argument "i" for "NoArguments"  [call-arg]
NoArguments(j=None)
# MYPY: error: Argument "j" to "NoArguments" has incompatible type "None"; expected "int"  [arg-type]
