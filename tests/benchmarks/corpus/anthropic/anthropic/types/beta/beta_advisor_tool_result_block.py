
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .beta_advisor_result_block import BetaAdvisorResultBlock
from .beta_advisor_tool_result_error import BetaAdvisorToolResultError
from .beta_advisor_redacted_result_block import BetaAdvisorRedactedResultBlock
Content: TypeAlias = Union[BetaAdvisorToolResultError, BetaAdvisorResultBlock, BetaAdvisorRedactedResultBlock]

class BetaAdvisorToolResultBlock(BaseModel):
    content: Content
    tool_use_id: str
    type: Literal['advisor_tool_result']
