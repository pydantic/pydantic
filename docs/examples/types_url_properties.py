from pydantic import BaseModel, HttpUrl, PostgresDsn, ValidationError, validator


class MyModel(BaseModel):
    url: HttpUrl


m = MyModel(url='http://www.example.com')

# the repr() method for a url will display all properties of the url
print(repr(m.url))
print(m.url.scheme)
print(m.url.host)
print(m.url.host_type)
print(m.url.port)


class MyDatabaseModel(BaseModel):
    db: PostgresDsn

    @validator('db')
    def check_db_name(cls, v):
        assert v.path and len(v.path) > 1, 'database must be provided'
        return v


m = MyDatabaseModel(db='postgres://user:pass@localhost:5432/foobar')
print(m.db)

try:
    MyDatabaseModel(db='postgres://user:pass@localhost:5432')
except ValidationError as e:
    print(e)
