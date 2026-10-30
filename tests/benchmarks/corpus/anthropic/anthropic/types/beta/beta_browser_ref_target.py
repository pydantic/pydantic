
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaBrowserRefTarget(BaseModel):
    """
    An element on the page, identified by a reference from a prior `read_page` or
    `find` result. References are scoped to the tab that produced them and become
    stale after navigation or a major re-render.
    """
    ref: str
    type: Literal['ref']
