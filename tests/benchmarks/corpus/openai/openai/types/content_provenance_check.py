# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .._utils import PropertyInfo
from .._models import BaseModel

class ResultC2PA(BaseModel):
    generated_at: Optional[str] = None
    issuer: Optional[str] = None
    model: Optional[str] = None
    outcome: Literal['detected', 'not_detected']
    type: Literal['c2pa']
    validation_state: Literal['trusted', 'valid', 'invalid', 'not_present']

class ResultSynthID(BaseModel):
    generated_at: Optional[str] = None
    model: Optional[str] = None
    outcome: Literal['detected', 'not_detected']
    type: Literal['synthid']
Result: TypeAlias = Annotated[Union[ResultC2PA, ResultSynthID], PropertyInfo(discriminator='type')]

class ContentProvenanceCheck(BaseModel):
    created_at: int
    object: Literal['content_provenance_check']
    results: List[Result]
