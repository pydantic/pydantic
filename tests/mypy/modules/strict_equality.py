from pydantic import BaseModel


class User(BaseModel):
    username: str


user = User(username='test')
print(user == 'test')
print(user.username == [1, 2, 3])
print(user.username == 'test')
