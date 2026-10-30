
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_url_document_source import BetaManagedAgentsURLDocumentSource
from .beta_managed_agents_file_document_source import BetaManagedAgentsFileDocumentSource
from .beta_managed_agents_base64_document_source import BetaManagedAgentsBase64DocumentSource
from .beta_managed_agents_plain_text_document_source import BetaManagedAgentsPlainTextDocumentSource
Source: TypeAlias = Annotated[Union[BetaManagedAgentsBase64DocumentSource, BetaManagedAgentsPlainTextDocumentSource, BetaManagedAgentsURLDocumentSource, BetaManagedAgentsFileDocumentSource], UnionDiscriminator('type')]

class BetaManagedAgentsDocumentBlock(BaseModel):
    """
    Document content, either specified directly as base64 data, as text, or as a reference via a URL.
    """
    source: Source
    type: Literal['document']
    context: Optional[str] = None
    title: Optional[str] = None
