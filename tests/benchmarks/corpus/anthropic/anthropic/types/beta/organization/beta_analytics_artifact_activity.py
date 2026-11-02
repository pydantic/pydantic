
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsArtifactActivity(BaseModel):
    """
    Artifact-creation activity for one (`artifact_type`, `is_shared`) bucket
    on a given day.

    Artifacts form a small finite cube — the canonical MIME type (8 values incl.
    `other`) crossed with shared-vs-private — so the response is the full set of
    non-empty buckets, not a ranked/paginated list. Claude Code and Cowork
    artifacts report under `text/html` and are counted from 2026-08-17
    onward; earlier days contain claude.ai chat artifacts only. With
    `group_by[]=product` / `user_id` / `rbac_group_id` each row is further
    split by the flat group keys and counts are scoped to that cut.
    """
    artifact_type: str
    artifacts_created_count: int
    distinct_user_count: int
    is_shared: bool
    published_artifacts_created_count: int
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    rbac_group_name: Optional[str] = None
    user_id: Optional[str] = None
