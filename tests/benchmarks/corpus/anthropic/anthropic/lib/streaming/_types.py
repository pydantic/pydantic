
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Generic
from typing_extensions import List, Literal
from ...types import Message, ContentBlock, RawMessageStopEvent, RawContentBlockStopEvent
from ..._models import BaseModel, GenericModel
from .._parse._response import ResponseFormatT
from ...types.parsed_message import ParsedMessage, ParsedContentBlock
from ...types.citations_delta import Citation

class TextEvent(BaseModel):
    type: Literal['text']
    text: str
    snapshot: str

class CitationEvent(BaseModel):
    type: Literal['citation']
    citation: Citation
    snapshot: List[Citation]

class ThinkingEvent(BaseModel):
    type: Literal['thinking']
    thinking: str
    snapshot: str

class SignatureEvent(BaseModel):
    type: Literal['signature']
    signature: str

class InputJsonEvent(BaseModel):
    type: Literal['input_json']
    partial_json: str
    snapshot: object

class MessageStopEvent(RawMessageStopEvent):
    type: Literal['message_stop']
    message: Message

class ContentBlockStopEvent(RawContentBlockStopEvent):
    type: Literal['content_block_stop']
    content_block: ContentBlock

class ParsedMessageStopEvent(RawMessageStopEvent, GenericModel, Generic[ResponseFormatT]):
    type: Literal['message_stop']
    message: ParsedMessage

class ParsedContentBlockStopEvent(RawContentBlockStopEvent, GenericModel, Generic[ResponseFormatT]):
    type: Literal['content_block_stop']
    content_block: ParsedContentBlock
