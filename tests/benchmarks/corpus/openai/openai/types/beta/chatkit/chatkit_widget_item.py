# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class ChatKitWidgetItem(BaseModel):
    """Thread item that renders a widget payload."""
    id: str
    created_at: int
    object: Literal['chatkit.thread_item']
    thread_id: str
    type: Literal['chatkit.widget']
    widget: str
