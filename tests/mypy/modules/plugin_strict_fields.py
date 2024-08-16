from pydantic import BaseModel, Field


class Model(BaseModel):
    a: int
    b: int = Field(strict=True)
    c: int = Field(strict=False)


# expected error: b
Model(a='1', b='2', c='3')


class ModelStrictMode(BaseModel):
    model_config = {'strict': True}

    a: int
    b: int = Field(strict=True)
    c: int = Field(strict=False)


# expected error: a, b
ModelStrictMode(a='1', b='2', c='3')


class ModelOverride1(Model):
    b: int = Field(strict=False)
    c: int = Field(strict=True)


# expected error: c
ModelOverride1(a='1', b='2', c='3')


class ModelOverride2(ModelStrictMode):
    b: int = Field(strict=False)
    c: int = Field(strict=True)


# expected error: a, c
ModelOverride2(a='1', b='2', c='3')


class ModelOverrideStrictMode(ModelStrictMode):
    model_config = {'strict': False}


# expected error: b
ModelOverrideStrictMode(a='1', b='2', c='3')
