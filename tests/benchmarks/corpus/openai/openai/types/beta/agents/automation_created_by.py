# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel

class AutomationCreatedByResourceDeveloper(BaseModel):
    type: Literal['developer']

class AutomationCreatedByResourceAgent(BaseModel):
    session_id: str
    tool_call_id: str
    type: Literal['agent']
AutomationCreatedBy: TypeAlias = Annotated[Union[AutomationCreatedByResourceDeveloper, AutomationCreatedByResourceAgent], PropertyInfo(discriminator='type')]
