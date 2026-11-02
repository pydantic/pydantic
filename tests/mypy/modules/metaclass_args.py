from pydantic import BaseModel, ConfigDict, Field


class ModelConfigUsed(BaseModel):
    i: int = Field(2, alias='j')

    model_config = ConfigDict(validate_by_name=True)


ModelConfigUsed(i=None)


class MetaclassArgumentsNoDefault(BaseModel, validate_by_name=True):
    i: int = Field(alias='j')


MetaclassArgumentsNoDefault(i=None)


class MetaclassArgumentsWithDefault(BaseModel, validate_by_name=True):
    i: int = Field(2, alias='j')


MetaclassArgumentsWithDefault(i=None)


class NoArguments(BaseModel):
    i: int = Field(2, alias='j')


NoArguments(i=1)
NoArguments(j=None)
