from typing_extensions import Literal

from pydantic import BaseModel, ValidationError


class Pie(BaseModel):
    flavor: Literal['apple', 'pumpkin']


Pie(flavor='apple')
Pie(flavor='pumpkin')
try:
    Pie(flavor='cherry')
except ValidationError as e:
    print(str(e))
"""
1 validation error
flavor
  unexpected value; permitted: 'apple', 'pumpkin' (type=value_error.const; given=cherry; permitted=('apple', 'pumpkin'))
"""
