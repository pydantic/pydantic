from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr = Field(..., exclude=...)


class Transaction(BaseModel):
    id: str
    user: User = Field(..., exclude={'username'})
    value: int

    class Config:
        fields = {'value': {'exclude': ...}}


t = Transaction(
    id='1234567890',
    user=User(
        id=42,
        username='JohnDoe',
        password='hashedpassword'
    ),
    value=9876543210,
)

print(t.dict())
