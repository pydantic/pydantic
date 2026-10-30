# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class SourceFileContentContent(BaseModel):
    item: Dict[str, object]
    sample: Optional[Dict[str, object]] = None

class SourceFileContent(BaseModel):
    content: List[SourceFileContentContent]
    type: Literal['file_content']

class SourceFileID(BaseModel):
    id: str
    type: Literal['file_id']
Source: TypeAlias = Annotated[Union[SourceFileContent, SourceFileID], PropertyInfo(discriminator='type')]

class CreateEvalJSONLRunDataSource(BaseModel):
    """
    A JsonlRunDataSource object with that specifies a JSONL file that matches the eval
    """
    source: Source
    type: Literal['jsonl']
