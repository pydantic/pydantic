
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class MemberRemoveResponse(BaseModel):
    type: Literal['workspace_member_deleted']
    user_id: str
    workspace_id: str
