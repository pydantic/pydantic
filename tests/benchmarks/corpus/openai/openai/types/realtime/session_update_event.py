# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .realtime_session_create_request import RealtimeSessionCreateRequest
from .realtime_transcription_session_create_request import RealtimeTranscriptionSessionCreateRequest
Session: TypeAlias = Union[RealtimeSessionCreateRequest, RealtimeTranscriptionSessionCreateRequest]

class SessionUpdateEvent(BaseModel):
    """
    Send this event to update the session’s configuration.
    The client may send this event at any time to update any field
    except for `voice` and `model`. `voice` can be updated only if there have been no other audio outputs yet.

    When the server receives a `session.update`, it will respond
    with a `session.updated` event showing the full, effective configuration.
    Only the fields that are present in the `session.update` are updated. To clear a field like
    `instructions`, pass an empty string. To clear a field like `tools`, pass an empty array.
    To clear a field like `turn_detection`, pass `null`.

    To turn off input audio noise reduction, send this Realtime event:

    ```json
    {"type":"session.update","session":{"type":"realtime","audio":{"input":{"noise_reduction":null}}}}
    ```

    For a transcription session, use `"type":"transcription"` inside `session`.
    Omitting `audio.input.noise_reduction` from an update leaves its current setting unchanged.
    """
    session: Session
    type: Literal['session.update']
    event_id: Optional[str] = None
