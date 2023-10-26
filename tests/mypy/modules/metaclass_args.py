from pydantic import BaseModel, Field


class ConfigClassUsed(BaseModel):
    i: int = Field(2, alias='j')

    class Config:
        populate_by_name = True


ConfigClassUsed(i=None)


class MetaclassArgumentsNoDefault(BaseModel, populate_by_name=True):
    i: int = Field(alias='j')


MetaclassArgumentsNoDefault(i=None)


class MetaclassArgumentsWithDefault(BaseModel, populate_by_name=True):
    i: int = Field(2, alias='j')


MetaclassArgumentsWithDefault(i=None)


class NoArguments(BaseModel):
    i: int = Field(2, alias='j')


NoArguments(i=1)
NoArguments(j=None)
