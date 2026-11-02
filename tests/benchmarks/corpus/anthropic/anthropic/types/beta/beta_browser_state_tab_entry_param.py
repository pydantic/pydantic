
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing_extensions import Required, TypedDict

class BetaBrowserStateTabEntryParam(TypedDict, total=False):
    """One open browser tab reported in a `browser_state` block's `tabs`
    inventory.

    `tab_id` is the caller-assigned identifier for the tab; `title` and
    `url` describe the page the tab is currently showing and may be empty
    strings (a blank tab legitimately has both empty). `active` marks the
    tab that is active after this call; whenever `tabs` is non-empty,
    exactly one entry is marked.
    """
    tab_id: Required[str]
    title: Required[str]
    url: Required[str]
    active: bool
