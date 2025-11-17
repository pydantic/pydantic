from pydantic import BaseModel


class User(BaseModel):
    username: str


user = User(username='test')
print(user == 'test')
print(user.username == int('1'))
print(user.username == 'test')
