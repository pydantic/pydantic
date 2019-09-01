from pydantic import BaseModel, HttpUrl, PostgresDsn, ValidationError, validator

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')

# the repr() method for a url will display all properties of the url
print(repr(m.url))
#>  <HttpUrl('http://www.example.com' scheme='http' host='www.example.com'
#>   tld='com' host_type='domain')>

print(m.url.scheme)
#>  http
print(m.url.host)
#>  www.example.com
print(m.url.host_type)
#>  domain
print(m.url.port)
#>  None

class MyDatabaseModel(BaseModel):
    db: PostgresDsn

    @validator('db')
    def check_db_name(cls, v):
        assert v.path and len(v.path) > 1, 'database must be provided'
        return v

m = MyDatabaseModel(db='postgres://user:pass@localhost:5432/foobar')
print(m.db)
#>  postgres://user:pass@localhost:5432/foobar

try:
    MyDatabaseModel(db='postgres://user:pass@localhost:5432')
except ValidationError as e:
    print(e)
"""
1 validation error for MyDatabaseModel
db
  database must be provided (type=assertion_error)
"""
