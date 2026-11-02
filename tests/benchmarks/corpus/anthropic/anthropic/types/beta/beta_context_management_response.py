
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_clear_thinking_20251015_edit_response import BetaClearThinking20251015EditResponse
from .beta_clear_tool_uses_20250919_edit_response import BetaClearToolUses20250919EditResponse
AppliedEdit: TypeAlias = Annotated[Union[BetaClearToolUses20250919EditResponse, BetaClearThinking20251015EditResponse], UnionDiscriminator('type')]

class BetaContextManagementResponse(BaseModel):
    applied_edits: List[AppliedEdit]
