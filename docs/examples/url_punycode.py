from pydantic import BaseModel, HttpUrl

class MyModel(BaseModel):
    url: HttpUrl

m1 = MyModel(url='http://puny£code.com')
print(m1.url)
#>  http://xn--punycode-eja.com
print(m1.url.host_type)
#>  int_domain

m2 = MyModel(url='https://www.аррӏе.com/')
print(m2.url)
#>  https://www.xn--80ak6aa92e.com/
print(m2.url.host_type)
#>  int_domain
