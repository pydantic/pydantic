
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsCoworkMetrics(BaseModel):
    """Cowork activity metrics for a single user on a given day."""
    action_count: int
    artifacts_created_count: int
    connectors_used_count: int
    dispatch_turn_count: int
    distinct_connectors_used_count: Optional[int] = None
    distinct_session_count: Optional[int] = None
    distinct_skills_used_count: Optional[int] = None
    message_count: int
    skills_used_count: int
    distinct_plugins_used_count: Optional[int] = None
    edit_tool_count: Optional[int] = None
    file_edit_count: Optional[int] = None
    multi_edit_tool_count: Optional[int] = None
    notebook_edit_tool_count: Optional[int] = None
    plugins_used_count: Optional[int] = None
    sessions_with_file_edits_count: Optional[int] = None
    write_tool_count: Optional[int] = None
