
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_telemetry_destination_test_failure import BetaTelemetryDestinationTestFailure
from .beta_telemetry_destination_test_success import BetaTelemetryDestinationTestSuccess
BetaTelemetryDestinationTestResult: TypeAlias = Annotated[Union[BetaTelemetryDestinationTestSuccess, BetaTelemetryDestinationTestFailure], UnionDiscriminator('type')]
