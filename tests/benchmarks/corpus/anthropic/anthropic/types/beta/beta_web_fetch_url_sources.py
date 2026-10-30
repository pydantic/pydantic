
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_web_fetch_url_source_all import BetaWebFetchURLSourceAll
from .beta_web_fetch_url_source_none import BetaWebFetchURLSourceNone
from .beta_web_fetch_url_source_only import BetaWebFetchURLSourceOnly
from .beta_web_fetch_url_source_except import BetaWebFetchURLSourceExcept
ClientToolResults: TypeAlias = Annotated[Union[BetaWebFetchURLSourceAll, BetaWebFetchURLSourceNone, BetaWebFetchURLSourceOnly, BetaWebFetchURLSourceExcept], UnionDiscriminator('type')]
ServerToolResults: TypeAlias = Annotated[Union[BetaWebFetchURLSourceAll, BetaWebFetchURLSourceNone, BetaWebFetchURLSourceOnly, BetaWebFetchURLSourceExcept], UnionDiscriminator('type')]
UserInput: TypeAlias = Annotated[Union[BetaWebFetchURLSourceAll, BetaWebFetchURLSourceNone], UnionDiscriminator('type')]

class BetaWebFetchURLSources(BaseModel):
    """Which sources contribute to the set of URLs web fetch may fetch.

    Each key is a tagged variant: ``user_input`` is ``all`` or ``none``; the
    two tool filters are ``all``, ``none``, ``only`` (only the named tools'
    results) or ``except`` (every result but the named tools'). A named tool
    must be declared in this request's ``tools[]``.
    """
    client_tool_results: Optional[ClientToolResults] = None
    server_tool_results: Optional[ServerToolResults] = None
    user_input: Optional[UserInput] = None
