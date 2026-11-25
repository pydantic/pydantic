
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import Field
from ...._models import BaseModel, UnionDiscriminator
from ....types.beta import BetaBrowserStateChangeParam, BetaBrowserStateTabEntryParam

def no_changes() -> list[StateChange]:
    return []

class BetaBrowserNavigateResult(BaseModel):
    """Where a navigation ended up. Rendered as `Navigated to {url} — {title} (HTTP {status})`, each value made safe
    for one line of text (control, line-separator and bidi characters replaced, length bounded)."""
    url: str
    status: int | None = None
    title: str | None = None

class BetaNavigationRefused(BaseModel):
    """A navigation the driver refused, for example a page-started navigation its request interception stopped.

    Its `type` is the SDK's own and is never sent: the SDK reports it to the model as one fixed line of text rather
    than in the `browser_state` block.
    """
    type: Literal['navigation_refused'] = 'navigation_refused'

class BetaDialogDismissed(BaseModel):
    """A native dialog (`alert`, `confirm`, `prompt`) the page opened and the driver dismissed.

    Its `type` is the SDK's own and is never sent: the SDK reports it to the model as a line of text with the next
    block (`A confirm dialog "Delete everything?" was dismissed.`), which tells the model the page asked and what the
    answer was. `message` is page-supplied text, capped when rendered.
    """
    type: Literal['dialog_dismissed'] = 'dialog_dismissed'
    kind: str
    message: str = ''
StateChange: TypeAlias = Annotated[BetaBrowserStateChangeParam | BetaNavigationRefused | BetaDialogDismissed, Field(discriminator='type'), UnionDiscriminator('type')]

class BetaBrowserState(BaseModel):
    """The browser after a call: what `_browser_state` returns. Forwarded to the API with download paths the file
    policy does not expose removed and each reported URL, title and error folded to one bounded line.

    `tabs` is the full inventory (the generated `BetaBrowserStateTabEntryParam`, with the active
    tab marked by its own `active` flag), `state_changes` what changed since the last report. The API's
    rules apply unchanged:

    - `tab_id` values are unique;
    - exactly one tab is `active` when any tab is open;
    - at most 100 tabs.

    Of the state changes, the SDK keeps the latest per `download_id` and one `tab_opened` per tab still open, so
    the list need not be deduplicated.
    """
    tabs: list[BetaBrowserStateTabEntryParam]
    state_changes: list[StateChange] = Field(default_factory=no_changes)
