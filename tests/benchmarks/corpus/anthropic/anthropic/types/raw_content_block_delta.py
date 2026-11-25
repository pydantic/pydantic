
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from .._models import UnionDiscriminator
from .text_delta import TextDelta
from .thinking_delta import ThinkingDelta
from .citations_delta import CitationsDelta
from .signature_delta import SignatureDelta
from .input_json_delta import InputJSONDelta
RawContentBlockDelta: TypeAlias = Annotated[Union[TextDelta, InputJSONDelta, CitationsDelta, ThinkingDelta, SignatureDelta], UnionDiscriminator('type')]
