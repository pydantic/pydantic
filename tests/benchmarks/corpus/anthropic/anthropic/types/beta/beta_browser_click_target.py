
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_browser_ref_target import BetaBrowserRefTarget
from .beta_browser_coordinate_target import BetaBrowserCoordinateTarget
BetaBrowserClickTarget: TypeAlias = Annotated[Union[BetaBrowserCoordinateTarget, BetaBrowserRefTarget], UnionDiscriminator('type')]
