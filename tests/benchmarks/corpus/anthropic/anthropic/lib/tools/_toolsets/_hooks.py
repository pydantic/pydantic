
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from ._inputs import BetaBrowserMemberName
from ._runnable import BetaToolsetCallContext
from ...._models import BaseModel
from ....types.beta import BetaBrowserMemberInput

class BetaURLContext(BaseModel):
    """What a hook receives about the call it serves: the first argument of `url_policy(context, url)` and of the
    file policy's `resolve_upload_paths(context, paths)` / `resolve_upload_documents(context, document_ids)`."""
    member: BetaBrowserMemberName | None = None
    tab_id: str | None = None
    tool_use_id: str | None = None

class BetaConfirmContext(BetaToolsetCallContext):
    """What `confirm` receives about the call awaiting approval: the member, its parsed input, and, through
    `tab_id` and `tab_url`, the tab the call targets (the active tab when it names none) as of the last
    `browser_state` report the SDK collected, with no page read; that is the report the model saw unless the
    call before failed. Both are `None` when that report has no such tab (anything before the first). `tab_url`
    is the URL as the model read it: the driver's string, folded to one line and held to 4,096 characters. An
    approval covers that report; the page is not read again after it. `input` holds a `file_upload`'s paths and
    document ids as the file policy returned them, and a `navigate` history word in lower case."""
    member: BetaBrowserMemberName
    input: BetaBrowserMemberInput
    tab_url: str | None = None
    tab_id: str | None = None
