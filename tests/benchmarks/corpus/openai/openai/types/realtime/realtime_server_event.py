# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .conversation_item import ConversationItem

class ConversationItemRetrieved(BaseModel):
    """Returned when a conversation item is retrieved with `conversation.item.retrieve`.

    This is provided as a way to fetch the server's representation of an item, for example to get access to the post-processed audio data after noise cancellation and VAD. It includes the full content of the Item, including audio data.
    """
    event_id: str
    item: ConversationItem
    type: Literal['conversation.item.retrieved']

class OutputAudioBufferStarted(BaseModel):
    """
    **WebRTC/SIP Only:** Emitted when the server begins streaming audio to the client. This event is
    emitted after an audio content part has been added (`response.content_part.added`)
    to the response.
    [Learn more](https://developers.openai.com/api/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc).
    """
    event_id: str
    response_id: str
    type: Literal['output_audio_buffer.started']

class OutputAudioBufferStopped(BaseModel):
    """
    **WebRTC/SIP Only:** Emitted when the output audio buffer has been completely drained on the server,
    and no more audio is forthcoming. This event is emitted after the full response
    data has been sent to the client (`response.done`).
    [Learn more](https://developers.openai.com/api/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc).
    """
    event_id: str
    response_id: str
    type: Literal['output_audio_buffer.stopped']

class OutputAudioBufferCleared(BaseModel):
    """**WebRTC/SIP Only:** Emitted when the output audio buffer is cleared.

    This happens either in VAD
    mode when the user has interrupted (`input_audio_buffer.speech_started`),
    or when the client has emitted the `output_audio_buffer.clear` event to manually
    cut off the current audio response.
    [Learn more](https://developers.openai.com/api/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc).
    """
    event_id: str
    response_id: str
    type: Literal['output_audio_buffer.cleared']
