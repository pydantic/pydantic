from pydantic import BaseModel, Field


class Model(BaseModel):
    a: int
    b: int = Field(strict=True)
    c: int = Field(strict=False)


# expected error: b
Model(a='1', b='2', c='3')
# MYPY: error: Argument "b" to "Model" has incompatible type "str"; expected "int"  [arg-type]


class ModelStrictMode(BaseModel):
    model_config = {'strict': True}

    a: int
    b: int = Field(strict=True)
    c: int = Field(strict=False)


# expected error: a, b
ModelStrictMode(a='1', b='2', c='3')
# MYPY: error: Argument "a" to "ModelStrictMode" has incompatible type "str"; expected "int"  [arg-type]
# MYPY: error: Argument "b" to "ModelStrictMode" has incompatible type "str"; expected "int"  [arg-type]


class ModelOverride1(Model):
    b: int = Field(strict=False)
    c: int = Field(strict=True)


# expected error: c
ModelOverride1(a='1', b='2', c='3')
# MYPY: error: Argument "c" to "ModelOverride1" has incompatible type "str"; expected "int"  [arg-type]


class ModelOverride2(ModelStrictMode):
    b: int = Field(strict=False)
    c: int = Field(strict=True)


# expected error: a, c
ModelOverride2(a='1', b='2', c='3')
# MYPY: error: Argument "a" to "ModelOverride2" has incompatible type "str"; expected "int"  [arg-type]
# MYPY: error: Argument "c" to "ModelOverride2" has incompatible type "str"; expected "int"  [arg-type]


class ModelOverrideStrictMode(ModelStrictMode):
    model_config = {'strict': False}


# expected error: b
ModelOverrideStrictMode(a='1', b='2', c='3')
# MYPY: error: Argument "b" to "ModelOverrideStrictMode" has incompatible type "str"; expected "int"  [arg-type]
