from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int = Field(..., include=True)
    username: str = Field(..., include=True)  # overridden by explicit include
    password: SecretStr


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

print(t.dict(include={'id': True, 'user': {'id'}}))
