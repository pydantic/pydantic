from pydantic import BaseModel, ConfigDict, Field


class ModelConfigUsed(BaseModel):
    i: int = Field(2, alias='j')

    model_config = ConfigDict(validate_by_name=True)


ModelConfigUsed(i=None)
# MYPY: error: Argument "i" to "ModelConfigUsed" has incompatible type "None"; expected "int"  [arg-type]


class MetaclassArgumentsNoDefault(BaseModel, validate_by_name=True):
    i: int = Field(alias='j')


MetaclassArgumentsNoDefault(i=None)
# MYPY: error: Argument "i" to "MetaclassArgumentsNoDefault" has incompatible type "None"; expected "int"  [arg-type]


class MetaclassArgumentsWithDefault(BaseModel, validate_by_name=True):
    i: int = Field(2, alias='j')


MetaclassArgumentsWithDefault(i=None)
# MYPY: error: Argument "i" to "MetaclassArgumentsWithDefault" has incompatible type "None"; expected "int"  [arg-type]


class NoArguments(BaseModel):
    i: int = Field(2, alias='j')


NoArguments(i=1)
# MYPY: error: Unexpected keyword argument "i" for "NoArguments"  [call-arg]
NoArguments(j=None)
# MYPY: error: Argument "j" to "NoArguments" has incompatible type "None"; expected "int"  [arg-type]
