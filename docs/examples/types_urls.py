from pydantic import BaseModel, HttpUrl, ValidationError


class MyModel(BaseModel):
    url: HttpUrl


m = MyModel(url='http://www.example.com')
print(m.url)

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)

try:
    MyModel(url='not a url')
except ValidationError as e:
    print(e)
