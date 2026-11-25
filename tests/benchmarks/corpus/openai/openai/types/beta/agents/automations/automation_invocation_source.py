# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel
from ..automation import Automation

class AutomationInvocationSourceResourceManual(BaseModel):
    type: Literal['manual']

class AutomationInvocationSourceResourceAutomation(BaseModel):
    automation: Automation
    type: Literal['automation']
AutomationInvocationSource: TypeAlias = Annotated[Union[AutomationInvocationSourceResourceManual, AutomationInvocationSourceResourceAutomation], PropertyInfo(discriminator='type')]
