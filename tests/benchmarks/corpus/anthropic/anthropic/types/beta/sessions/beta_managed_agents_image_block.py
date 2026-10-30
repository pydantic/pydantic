
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_url_image_source import BetaManagedAgentsURLImageSource
from .beta_managed_agents_file_image_source import BetaManagedAgentsFileImageSource
from .beta_managed_agents_base64_image_source import BetaManagedAgentsBase64ImageSource
Source: TypeAlias = Annotated[Union[BetaManagedAgentsBase64ImageSource, BetaManagedAgentsURLImageSource, BetaManagedAgentsFileImageSource], UnionDiscriminator('type')]

class BetaManagedAgentsImageBlock(BaseModel):
    """Image content specified directly as base64 data or as a reference via a URL."""
    source: Source
    type: Literal['image']
