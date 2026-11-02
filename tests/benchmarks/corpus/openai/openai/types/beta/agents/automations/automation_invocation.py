# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel
from .automation_invocation_source import AutomationInvocationSource

class Error(BaseModel):
    """The permanent delivery failure, or null when no failure occurred."""
    code: str
    message: str

class AutomationInvocation(BaseModel):
    """One attempted delivery by an automation."""
    id: str
    automation_id: str
    created_at: int
    error: Optional[Error] = None
    object: Literal['agent.automation.invocation']
    scheduled_at: Optional[int] = None
    session_id: Optional[str] = None
    skip_reason: Optional[Literal['pending_delivery']] = None
    source: AutomationInvocationSource
    status: Literal['queued', 'completed', 'failed', 'skipped']
