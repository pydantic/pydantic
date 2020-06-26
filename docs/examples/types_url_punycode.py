from pydantic import BaseModel, HttpUrl


class MyModel(BaseModel):
    url: HttpUrl


m1 = MyModel(url='http://puny£code.com')
print(m1.url)
print(m1.url.host_type)
m2 = MyModel(url='https://www.аррӏе.com/')
print(m2.url)
print(m2.url.host_type)
m3 = MyModel(url='https://www.example.珠宝/')
print(m3.url)
print(m3.url.host_type)
