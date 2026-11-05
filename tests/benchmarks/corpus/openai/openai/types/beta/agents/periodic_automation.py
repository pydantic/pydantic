# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict
from typing_extensions import Literal
from ...._models import BaseModel
from .automation_target import AutomationTarget
from .automation_created_by import AutomationCreatedBy

class PeriodicAutomation(BaseModel):
    """Fields shared by periodic and one-time automations."""
    id: str
    created_at: int
    created_by: AutomationCreatedBy
    expression: str
    metadata: Dict[str, str]
    name: str
    object: Literal['agent.automation']
    status: Literal['active', 'paused']
    target: AutomationTarget
    timezone: str
    type: Literal['periodic']
