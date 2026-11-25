
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from .._models import UnionDiscriminator
from .browser_ref_target import BrowserRefTarget
from .browser_coordinate_target import BrowserCoordinateTarget
BrowserClickTarget: TypeAlias = Annotated[Union[BrowserCoordinateTarget, BrowserRefTarget], UnionDiscriminator('type')]
