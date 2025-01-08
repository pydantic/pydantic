Pydantic serves as a great tool for defining models for ORM (object relational mapping) libraries.
ORMs are used to map objects to database tables, and vice versa.

## SQLAlchemy

Pydantic can pair with SQLAlchemy, as it can be used to define the schema of the database models.

!!! warning "Code Duplication"
    If you use Pydantic with SQLAlchemy, you might experience some frustration with code duplication.
    If you find yourself experiencing this difficulty, you might also consider [`SQLModel`](https://sqlmodel.tiangolo.com/) which integrates Pydantic with SQLAlchemy such that much of the code duplication is eliminated.

If you'd prefer to use pure Pydantic with SQLAlchemy, we recommend using Pydantic models alongside of SQLAlchemy models
as shown in the example below. In this case, we take advantage of Pydantic's aliases feature to name a `Column` after a reserved SQLAlchemy field, thus avoiding conflicts.

```python
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

<!-- TODO: add examples for Django with Pydantic models -->
