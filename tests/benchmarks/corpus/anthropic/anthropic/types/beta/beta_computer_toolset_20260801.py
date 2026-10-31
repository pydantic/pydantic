
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral
from .beta_computer_toolset_configs import BetaComputerToolsetConfigs

class BetaComputerToolset20260801(BaseModel):
    """
    The computer toolset: a single ``tools[]`` entry (carrying no
    ``name``) that declares the computer tool family. The model is
    served the family's tool with any members disabled via ``configs``
    removed from its schema. Every member is enabled by default, zoom
    included. The single-tool options ``display_number`` and
    ``enable_zoom`` are not fields of a toolset entry — it carries only
    ``type``, ``configs``, and ``cache_control``; zoom is controlled
    via ``configs.zoom.enabled``.
    """
    type: Literal['computer_toolset_20260801']
    cache_control: Optional[BetaCacheControlEphemeral] = None
    configs: Optional[BetaComputerToolsetConfigs] = None
