
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_citation_config import BetaCitationConfig
from .beta_base64_pdf_source import BetaBase64PDFSource
from .beta_plain_text_source import BetaPlainTextSource
Source: TypeAlias = Annotated[Union[BetaBase64PDFSource, BetaPlainTextSource], UnionDiscriminator('type')]

class BetaDocumentBlock(BaseModel):
    citations: Optional[BetaCitationConfig] = None
    source: Source
    title: Optional[str] = None
    type: Literal['document']
