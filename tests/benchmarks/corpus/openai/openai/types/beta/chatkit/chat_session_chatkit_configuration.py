# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ...._models import BaseModel
from .chat_session_history import ChatSessionHistory
from .chat_session_file_upload import ChatSessionFileUpload
from .chat_session_automatic_thread_titling import ChatSessionAutomaticThreadTitling

class ChatSessionChatKitConfiguration(BaseModel):
    """ChatKit configuration for the session."""
    automatic_thread_titling: ChatSessionAutomaticThreadTitling
    file_upload: ChatSessionFileUpload
    history: ChatSessionHistory
