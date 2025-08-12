from pydantic import BaseModel


class User(BaseModel):
    username: str


user = User(username='test')
print(user == 'test')
# MYPY: error: Non-overlapping equality check (left operand type: "User", right operand type: "Literal['test']")  [comparison-overlap]
print(user.username == int('1'))
# MYPY: error: Non-overlapping equality check (left operand type: "str", right operand type: "int")  [comparison-overlap]
print(user.username == 'test')
