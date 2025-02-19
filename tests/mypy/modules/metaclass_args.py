from pydantic import BaseModel, Field


class ConfigClassUsed(BaseModel):
    i: int = Field(2, alias='j')

    class Config:
        validate_by_name = True


ConfigClassUsed(i=None)


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
