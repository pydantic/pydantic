
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_thinking_dropped_input_transformation import BetaThinkingDroppedInputTransformation
from .beta_thinking_mismatch_allowed_input_transformation import BetaThinkingMismatchAllowedInputTransformation
BetaInputTransformation: TypeAlias = Annotated[Union[BetaThinkingDroppedInputTransformation, BetaThinkingMismatchAllowedInputTransformation], UnionDiscriminator('type')]
