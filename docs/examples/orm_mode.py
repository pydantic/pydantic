from typing import List
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, constr

Base = declarative_base()

class CompanyOrm(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, nullable=False)
    public_key = Column(String(20), index=True, nullable=False, unique=True)
    name = Column(String(63), unique=True)
    domains = Column(ARRAY(String(255)))

class CompanyModel(BaseModel):
    id: int
    public_key: constr(max_length=20)
    name: constr(max_length=63)
    domains: List[constr(max_length=255)]

    class Config:
        orm_mode = True

co_orm = CompanyOrm(
    id=123,
    public_key='foobar',
    name='Testing',
    domains=['example.com', 'foobar.com']
)
print(co_orm)
#> <__main__.CompanyOrm object at 0x7ff4bf918278>
co_model = CompanyModel.from_orm(co_orm)
print(co_model)
#> CompanyModel id=123
#>              public_key='foobar'
#>              name='Testing'
#>              domains=['example.com', 'foobar.com']
