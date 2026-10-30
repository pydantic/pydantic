
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebFetchURLSourceAll(BaseModel):
    """
    The ``url_sources`` variant under which a source contributes in
    full: every result of the tool filter's source, or all user input.
    """
    type: Literal['all']
