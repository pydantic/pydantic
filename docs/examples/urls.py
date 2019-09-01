from pydantic import BaseModel, HttpUrl, ValidationError

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')
print(m.url)
#> http://www.example.com

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)

"""
1 validation error for MyModel
url
  URL scheme not permitted (type=value_error.url.scheme; 
      allowed_schemes={'http', 'https'})
"""
