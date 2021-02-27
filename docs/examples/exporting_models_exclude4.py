from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str  # overridden by explicit exclude
    password: SecretStr = Field(exclude=True)


class Transaction(BaseModel):
    id: str
    user: User
    value: int


t = Transaction(
    id='1234567890',
    user=User(
        id=42,
        username='JohnDoe',
        password='hashedpassword'
    ),
    value=9876543210,
)

print(t.dict(exclude={'value': True, 'user': {'username'}}))
