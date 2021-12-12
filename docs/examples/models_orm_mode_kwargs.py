import typing

from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


class MyModel(BaseModel):
    metadata: typing.Dict[str, str]

    class Config:
        orm_mode = True


BaseModel = declarative_base()


class SQLModel(BaseModel):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' is reserved by SQLAlchemy, hence the '_'
    metadata_ = sa.Column('metadata', sa.JSON)


sql_model = SQLModel(metadata_={'key': 'val'}, id=1)

# notice that we are explicitly setting the value of 'metadata'
pydantic_model = MyModel.from_orm(sql_model, metadata=sql_model.metadata_)

print(pydantic_model.dict())
print(pydantic_model.dict(by_alias=True))
