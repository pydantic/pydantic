
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Generic
from typing_extensions import List, Literal
from ..._models import BaseModel, GenericModel
from ...types.beta import BetaRawMessageStopEvent, BetaRawContentBlockStopEvent
from .._parse._response import ResponseFormatT
from ...types.beta.parsed_beta_message import ParsedBetaMessage, ParsedBetaContentBlock
from ...types.beta.beta_citations_delta import Citation

class ParsedBetaTextEvent(BaseModel):
    type: Literal['text']
    text: str
    snapshot: str

class BetaCitationEvent(BaseModel):
    type: Literal['citation']
    citation: Citation
    snapshot: List[Citation]

class BetaThinkingEvent(BaseModel):
    type: Literal['thinking']
    thinking: str
    snapshot: str

class BetaSignatureEvent(BaseModel):
    type: Literal['signature']
    signature: str

class BetaInputJsonEvent(BaseModel):
    type: Literal['input_json']
    partial_json: str
    snapshot: object

class BetaCompactionEvent(BaseModel):
    type: Literal['compaction']
    content: Union[str, None]
    encrypted_content: Union[str, None]

class ParsedBetaMessageStopEvent(BetaRawMessageStopEvent, GenericModel, Generic[ResponseFormatT]):
    type: Literal['message_stop']
    message: ParsedBetaMessage

class ParsedBetaContentBlockStopEvent(BetaRawContentBlockStopEvent, GenericModel, Generic[ResponseFormatT]):
    type: Literal['content_block_stop']
    content_block: ParsedBetaContentBlock
