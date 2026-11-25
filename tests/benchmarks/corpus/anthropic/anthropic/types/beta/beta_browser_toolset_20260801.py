
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_browser_toolset_configs import BetaBrowserToolsetConfigs
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaBrowserToolset20260801(BaseModel):
    """
    The browser toolset: a single ``tools[]`` entry (carrying no
    ``name``) that declares the browser tool family. The model is served
    the family's tool with any members disabled via ``configs`` removed
    from its schema.
    """
    type: Literal['browser_toolset_20260801']
    cache_control: Optional[BetaCacheControlEphemeral] = None
    configs: Optional[BetaBrowserToolsetConfigs] = None
