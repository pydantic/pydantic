
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_analytics_api_actor import BetaAnalyticsAPIActor
from .beta_analytics_federated_actor import BetaAnalyticsFederatedActor
from .beta_analytics_report_user_actor import BetaAnalyticsReportUserActor
from .beta_analytics_service_account_actor import BetaAnalyticsServiceAccountActor
BetaAnalyticsActor: TypeAlias = Annotated[Union[BetaAnalyticsReportUserActor, BetaAnalyticsServiceAccountActor, BetaAnalyticsFederatedActor, BetaAnalyticsAPIActor], UnionDiscriminator('type')]
