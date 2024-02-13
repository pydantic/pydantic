from pydantic import BaseModel


class User(BaseModel):
    username: str


user = User(username='test')
print(user == 'test')
# MYPY: error: Non-overlapping equality check (left operand type: "User", right operand type: "Literal['test']")  [comparison-overlap]
print(user.username == [1, 2, 3])
# MYPY: error: Non-overlapping equality check (left operand type: "str", right operand type: "List[int]")  [comparison-overlap]
print(user.username == 'test')
