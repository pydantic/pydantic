
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
from .citations_config import CitationsConfig
from .base64_pdf_source import Base64PDFSource
from .plain_text_source import PlainTextSource
Source: TypeAlias = Annotated[Union[Base64PDFSource, PlainTextSource], UnionDiscriminator('type')]

class DocumentBlock(BaseModel):
    citations: Optional[CitationsConfig] = None
    source: Source
    title: Optional[str] = None
    type: Literal['document']
