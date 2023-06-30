from pydantic import BaseModel, Field


class ConfigClassUsed(BaseModel):
    i: int = Field(2, alias='j')

    class Config:
        populate_by_name = True


ConfigClassUsed(i=None)
# MYPY: error: Argument "i" to "ConfigClassUsed" has incompatible type "None"; expected "int"  [arg-type]


class MetaclassArgumentsNoDefault(BaseModel, populate_by_name=True):
    i: int = Field(alias='j')


MetaclassArgumentsNoDefault(i=None)
# MYPY: error: Argument "i" to "MetaclassArgumentsNoDefault" has incompatible type "None"; expected "int"  [arg-type]


class MetaclassArgumentsWithDefault(BaseModel, populate_by_name=True):
    i: int = Field(2, alias='j')


MetaclassArgumentsWithDefault(i=None)
# MYPY: error: Argument "i" to "MetaclassArgumentsWithDefault" has incompatible type "None"; expected "int"  [arg-type]


class NoArguments(BaseModel):
    i: int = Field(2, alias='j')


NoArguments(i=1)
# MYPY: error: Unexpected keyword argument "i" for "NoArguments"  [call-arg]
NoArguments(j=None)
# MYPY: error: Argument "j" to "NoArguments" has incompatible type "None"; expected "int"  [arg-type]
