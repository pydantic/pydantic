from pydantic import BaseModel, SecretStr, SecretBytes, ValidationError


class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes


sm = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm)
print(sm.password)
print(sm.dict())
print(sm.json())

# Use get_secret_value method to see the secret's content.
print(sm.password.get_secret_value())
print(sm.password_bytes.get_secret_value())

try:
    SimpleModel(password=[1, 2, 3], password_bytes=[1, 2, 3])
except ValidationError as e:
    print(e)


# If you want the secret to be dumped as plain-text using the json method,
# you can use json_encoders in the Config class.
class SimpleModelDumpable(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
            SecretBytes: lambda v: v.get_secret_value() if v else None,
        }


sm2 = SimpleModelDumpable(
    password='IAmSensitive', password_bytes=b'IAmSensitiveBytes'
)

# Standard access methods will not display the secret
print(sm2)
print(sm2.password)
print(sm2.dict())

# But the json method will
print(sm2.json())
