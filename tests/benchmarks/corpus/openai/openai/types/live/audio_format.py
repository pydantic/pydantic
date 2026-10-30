# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class AudioPCM(BaseModel):
    """Raw, mono 16-bit little-endian PCM audio for a Live WebSocket connection."""
    rate: Literal[16000, 24000]
    type: Literal['audio/pcm']

class AudioPCMU(BaseModel):
    """Raw, mono G.711 μ-law audio for a Live WebSocket connection."""
    rate: int
    type: Literal['audio/pcmu']

class AudioPCMA(BaseModel):
    """Raw, mono G.711 A-law audio for a Live WebSocket connection."""
    rate: int
    type: Literal['audio/pcma']
AudioFormat: TypeAlias = Annotated[Union[AudioPCM, AudioPCMU, AudioPCMA], PropertyInfo(discriminator='type')]
