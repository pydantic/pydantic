from pydantic import BaseModel, ByteSize


class MyModel(BaseModel):
    size: ByteSize


print(MyModel(size=52000).size)
print(MyModel(size='3000 KiB').size)

m = MyModel(size='50 PB')
print(m.size.human_readable())
print(m.size.human_readable(decimal=True))

print(m.size.to('TiB'))
