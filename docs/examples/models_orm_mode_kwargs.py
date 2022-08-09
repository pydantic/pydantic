from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


class MyModel(BaseModel):
    foo: str
    bar: int
    spam: bytes

    class Config:
        orm_mode = True


BaseModel = declarative_base()


class SQLModel(BaseModel):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    foo = sa.Column('foo', sa.String(32))
    bar = sa.Column('bar', sa.Integer)


sql_model = SQLModel(id=1, foo='hello world', bar=123)

pydantic_model = MyModel.from_orm(sql_model, bar=456, spam=b'placeholder')

print(pydantic_model.dict())
print(pydantic_model.dict(by_alias=True))
