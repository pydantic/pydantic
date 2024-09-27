!!! warning "🚧 Work in Progress"
    This page is a work in progress. More examples will be added soon.

Pydantic serves as a great tool for defining models for ORM (object relational mapping) libraries.
ORMs are used to map objects to database tables, and vice versa.

## SQLAlchemy

Pydantic pairs quite well with SQLAlchemy, as it can be used to define the schema of the database models.

Here's a simple example of how you can use a Pydantic model to validate data from a SQLAlchemy model.
In this example, we take advantage of field aliases to name a `Column` after a reserved SQLAlchemy field, thus avoiding conflicts.

```py
import typing

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from pydantic import BaseModel, ConfigDict, Field


class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: typing.Dict[str, str] = Field(alias='metadata_')


Base = declarative_base()


class MyTableModel(Base):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' is reserved by SQLAlchemy, hence the '_'
    metadata_ = sa.Column('metadata', sa.JSON)


sql_model = MyTableModel(metadata_={'key': 'val'}, id=1)
pydantic_model = MyModel.model_validate(sql_model)

print(pydantic_model.model_dump())
#> {'metadata': {'key': 'val'}}
print(pydantic_model.model_dump(by_alias=True))
#> {'metadata_': {'key': 'val'}}
```

!!! note
    The example above works because aliases have priority over field names for
    field population. Accessing `SQLModel`'s `metadata` attribute would lead to a `ValidationError`.

!!! note
    You might also consider [`SQLModel`](https://sqlmodel.tiangolo.com/) which integrates Pydantic with SQLAlchemy.

<!-- TODO: add examples for Django with Pydantic models -->
