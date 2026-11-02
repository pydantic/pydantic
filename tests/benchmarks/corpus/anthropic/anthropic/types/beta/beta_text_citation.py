
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_citation_char_location import BetaCitationCharLocation
from .beta_citation_page_location import BetaCitationPageLocation
from .beta_citation_content_block_location import BetaCitationContentBlockLocation
from .beta_citation_search_result_location import BetaCitationSearchResultLocation
from .beta_citations_web_search_result_location import BetaCitationsWebSearchResultLocation
BetaTextCitation: TypeAlias = Annotated[Union[BetaCitationCharLocation, BetaCitationPageLocation, BetaCitationContentBlockLocation, BetaCitationsWebSearchResultLocation, BetaCitationSearchResultLocation], UnionDiscriminator('type')]
