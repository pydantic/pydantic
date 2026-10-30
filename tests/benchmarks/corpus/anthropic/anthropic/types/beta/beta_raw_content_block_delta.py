
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_text_delta import BetaTextDelta
from .beta_thinking_delta import BetaThinkingDelta
from .beta_citations_delta import BetaCitationsDelta
from .beta_signature_delta import BetaSignatureDelta
from .beta_input_json_delta import BetaInputJSONDelta
from .beta_compaction_content_block_delta import BetaCompactionContentBlockDelta
BetaRawContentBlockDelta: TypeAlias = Annotated[Union[BetaTextDelta, BetaInputJSONDelta, BetaCitationsDelta, BetaThinkingDelta, BetaSignatureDelta, BetaCompactionContentBlockDelta], UnionDiscriminator('type')]
