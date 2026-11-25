
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel
from .message_batch_result import MessageBatchResult

class MessageBatchIndividualResponse(BaseModel):
    """
    This is a single line in the response `.jsonl` file and does not represent the response as a whole.
    """
    custom_id: str
    result: MessageBatchResult
