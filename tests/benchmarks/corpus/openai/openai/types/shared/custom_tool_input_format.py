# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class Text(BaseModel):
    """Unconstrained free-form text."""
    type: Literal['text']

class Grammar(BaseModel):
    """A grammar defined by the user."""
    definition: str
    syntax: Literal['lark', 'regex']
    type: Literal['grammar']
CustomToolInputFormat: TypeAlias = Annotated[Union[Text, Grammar], PropertyInfo(discriminator='type')]
