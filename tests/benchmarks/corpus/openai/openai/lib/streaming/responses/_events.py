
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from __future__ import annotations
from typing import Optional
from typing_extensions import Generic, TypeVar
from ...._compat import GenericModel
from ....types.responses import ParsedResponse, ResponseTextDoneEvent as RawResponseTextDoneEvent, ResponseCompletedEvent as RawResponseCompletedEvent, ResponseTextDeltaEvent as RawResponseTextDeltaEvent, ResponseFunctionCallArgumentsDeltaEvent as RawResponseFunctionCallArgumentsDeltaEvent
TextFormatT = TypeVar('TextFormatT', default=None)

class ResponseTextDeltaEvent(RawResponseTextDeltaEvent):
    snapshot: str

class ResponseTextDoneEvent(RawResponseTextDoneEvent, GenericModel, Generic[TextFormatT]):
    parsed: Optional[TextFormatT] = None

class ResponseFunctionCallArgumentsDeltaEvent(RawResponseFunctionCallArgumentsDeltaEvent):
    snapshot: str

class ResponseCompletedEvent(RawResponseCompletedEvent, GenericModel, Generic[TextFormatT]):
    response: ParsedResponse[TextFormatT]
