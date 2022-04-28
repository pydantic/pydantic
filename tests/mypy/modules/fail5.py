from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    name: str
    postal: Optional[int]


# ok
Model(name='foo').shallow_copy()
Model(name='foo').shallow_copy(name='name')
Model(name='foo').shallow_copy(postal=123)
Model(name='foo').shallow_copy(postal=None)
Model(name='foo').deep_copy()
Model(name='foo').deep_copy(name='name')
Model(name='foo').deep_copy(postal=123)
Model(name='foo').deep_copy(postal=None)

# fails
Model(name='foo').shallow_copy(weq=1)
Model(name='foo').shallow_copy(postal='postal')
Model(name='foo').shallow_copy(name=1)
Model(name='foo').deep_copy(weq=1)
Model(name='foo').deep_copy(postal='postal')
Model(name='foo').deep_copy(name=1)
