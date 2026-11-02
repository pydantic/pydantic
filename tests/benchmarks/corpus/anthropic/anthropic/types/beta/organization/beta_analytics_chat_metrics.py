
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsChatMetrics(BaseModel):
    """Claude.ai activity metrics for a single user on a given day."""
    connectors_used_count: int
    distinct_artifacts_created_count: int
    distinct_connectors_used_count: Optional[int] = None
    distinct_conversation_count: Optional[int] = None
    distinct_files_uploaded_count: Optional[int] = None
    distinct_projects_created_count: int
    distinct_projects_used_count: Optional[int] = None
    distinct_shared_artifacts_viewed_count: Optional[int] = None
    distinct_skills_used_count: Optional[int] = None
    message_count: int
    shared_conversations_viewed_count: int
    thinking_message_count: int
