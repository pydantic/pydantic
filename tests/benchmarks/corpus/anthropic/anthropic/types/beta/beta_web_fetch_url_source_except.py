
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_web_fetch_url_source_tool_reference import BetaWebFetchURLSourceToolReference

class BetaWebFetchURLSourceExcept(BaseModel):
    """
    The tool filter variant under which every result but the named
    tools' contributes.
    """
    tools: List[BetaWebFetchURLSourceToolReference]
    type: Literal['except']
