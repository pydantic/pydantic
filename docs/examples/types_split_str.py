from pydantic import (
    BaseModel,
    CommaSeparated,
    CommaSeparatedStripped,
    SpaceSeparated
)


class Model(BaseModel):
    comma_separated: CommaSeparated[int]
    space_separated: SpaceSeparated[float]
    comma_separated_stripped: CommaSeparatedStripped[str]


model = Model(
    comma_separated='1,2,345,678',
    space_separated='2 3.45 4.678 0',
    comma_separated_stripped='Samuel, David, Sebastián'
)

print(model)
