
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_telemetry_destination_workspaces_all import BetaTelemetryDestinationWorkspacesAll
from .beta_telemetry_destination_workspaces_exclude import BetaTelemetryDestinationWorkspacesExclude
from .beta_telemetry_destination_workspaces_include import BetaTelemetryDestinationWorkspacesInclude
BetaTelemetryDestinationWorkspaces: TypeAlias = Annotated[Union[BetaTelemetryDestinationWorkspacesAll, BetaTelemetryDestinationWorkspacesInclude, BetaTelemetryDestinationWorkspacesExclude], UnionDiscriminator('type')]
