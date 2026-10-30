
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaWorkspaceRole: TypeAlias = Literal['workspace_admin', 'workspace_billing', 'workspace_developer', 'workspace_restricted_developer', 'workspace_user']
