# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Generic, Literal, TypeVar
from pydantic import BaseModel
ElicitSchemaModelT = TypeVar('ElicitSchemaModelT', bound=BaseModel)

class AcceptedElicitation(BaseModel, Generic[ElicitSchemaModelT]):
    action: Literal['accept'] = 'accept'
    data: ElicitSchemaModelT

class DeclinedElicitation(BaseModel):
    action: Literal['decline'] = 'decline'

class CancelledElicitation(BaseModel):
    action: Literal['cancel'] = 'cancel'

class AcceptedUrlElicitation(BaseModel):
    action: Literal['accept'] = 'accept'
