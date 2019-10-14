from pydantic import BaseModel, SecretStr, SecretBytes, ValidationError

class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

sm = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')
print(sm)

print(sm.password.get_secret_value())
print(sm.password_bytes.get_secret_value())
print(sm.password.display())
print(sm.json())


try:
    SimpleModel(password=[1, 2, 3], password_bytes=[1, 2, 3])
except ValidationError as e:
    print(e)
