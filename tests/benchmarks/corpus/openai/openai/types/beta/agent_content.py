# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .output_text import OutputText

class EncryptedContentResource(BaseModel):
    """Encrypted content exchanged between agents."""
    encrypted_content: str
    type: Literal['encrypted_content']
AgentContent: TypeAlias = Annotated[Union[OutputText, EncryptedContentResource], PropertyInfo(discriminator='type')]
