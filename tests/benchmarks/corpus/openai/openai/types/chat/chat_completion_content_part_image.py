# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ImageURL(BaseModel):
    url: str
    detail: Optional[Literal['auto', 'low', 'high', 'original']] = None

class PromptCacheBreakpoint(BaseModel):
    """Marks the exact end of a reusable prompt prefix.

    When `ttl` is omitted, the breakpoint inherits the request's `prompt_cache_options.ttl`; the boundary is not rounded to a token block.
    """
    mode: Literal['explicit']
    ttl: Optional[Literal['30m', '12h']] = None

class ChatCompletionContentPartImage(BaseModel):
    """
    Learn about [image inputs](https://developers.openai.com/api/docs/guides/images-vision).
    """
    image_url: ImageURL
    type: Literal['image_url']
    prompt_cache_breakpoint: Optional[PromptCacheBreakpoint] = None
