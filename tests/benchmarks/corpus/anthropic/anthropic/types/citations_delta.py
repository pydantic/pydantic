
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
from .citation_char_location import CitationCharLocation
from .citation_page_location import CitationPageLocation
from .citation_content_block_location import CitationContentBlockLocation
from .citations_search_result_location import CitationsSearchResultLocation
from .citations_web_search_result_location import CitationsWebSearchResultLocation
Citation: TypeAlias = Annotated[Union[CitationCharLocation, CitationPageLocation, CitationContentBlockLocation, CitationsWebSearchResultLocation, CitationsSearchResultLocation], UnionDiscriminator('type')]

class CitationsDelta(BaseModel):
    citation: Citation
    type: Literal['citations_delta']
