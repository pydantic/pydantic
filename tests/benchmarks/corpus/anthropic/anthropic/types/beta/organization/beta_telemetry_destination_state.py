
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_telemetry_destination_state_enabled import BetaTelemetryDestinationStateEnabled
from .beta_telemetry_destination_state_disabled import BetaTelemetryDestinationStateDisabled
BetaTelemetryDestinationState: TypeAlias = Annotated[Union[BetaTelemetryDestinationStateEnabled, BetaTelemetryDestinationStateDisabled], UnionDiscriminator('type')]
