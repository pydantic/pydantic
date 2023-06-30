from pydantic import BaseModel


class Person(BaseModel):
    id: int
    name: str
    birth_year: int

    def __init__(self, id: int) -> None:
# MYPY: note: "Person" defined here
        super().__init__(id=id, name='Patrick', birth_year=1991)


Person(1)
Person(id=1)
Person(name='Patrick')
# MYPY: error: Unexpected keyword argument "name" for "Person"  [call-arg]
