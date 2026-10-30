
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaClaudeTagDefaultSettingSource(BaseModel):
    """No settings level sets a value, and the built-in default applies."""
    type: Literal['default']
