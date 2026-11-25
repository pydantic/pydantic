# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_image_detail import BetaImageDetail

class PromptCacheBreakpoint(BaseModel):
    """Marks the exact end of a reusable prompt prefix.

    When `ttl` is omitted, the breakpoint inherits the request's `prompt_cache_options.ttl`; the boundary is not rounded to a token block.
    """
    mode: Literal['explicit']
    ttl: Optional[Literal['30m', '12h']] = None

class BetaResponseInputImageContent(BaseModel):
    """An image input to the model.

    Learn about [image inputs](https://developers.openai.com/api/docs/guides/images-vision)
    """
    type: Literal['input_image']
    detail: Optional[BetaImageDetail] = None
    file_id: Optional[str] = None
    image_url: Optional[str] = None
    prompt_cache_breakpoint: Optional[PromptCacheBreakpoint] = None
