# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class ServerVad(BaseModel):
    """
    Server-side voice activity detection (VAD) which flips on when user speech is detected and off after a period of silence.
    """
    type: Literal['server_vad']
    create_response: Optional[bool] = None
    idle_timeout_ms: Optional[int] = None
    interrupt_response: Optional[bool] = None
    prefix_padding_ms: Optional[int] = None
    silence_duration_ms: Optional[int] = None
    threshold: Optional[float] = None

class SemanticVad(BaseModel):
    """
    Server-side semantic turn detection which uses a model to determine when the user has finished speaking.
    """
    type: Literal['semantic_vad']
    create_response: Optional[bool] = None
    eagerness: Optional[Literal['low', 'medium', 'high', 'auto']] = None
    interrupt_response: Optional[bool] = None
RealtimeAudioInputTurnDetection: TypeAlias = Annotated[Union[ServerVad, SemanticVad, None], PropertyInfo(discriminator='type')]
