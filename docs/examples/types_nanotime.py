from pydantic import BaseModel, NanoTime


class MyModel(BaseModel):
    time: NanoTime


print(MyModel(time=int(1.5e6)).time)
print(MyModel(time='15m 30s').time)

m = MyModel(time='2.2d')
print(m.time.human_readable())

print(m.time.to('h'))
