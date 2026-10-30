# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class TextSimilarityGrader(BaseModel):
    """A TextSimilarityGrader object which grades text based on similarity metrics."""
    evaluation_metric: Literal['cosine', 'fuzzy_match', 'bleu', 'gleu', 'meteor', 'rouge_1', 'rouge_2', 'rouge_3', 'rouge_4', 'rouge_5', 'rouge_l']
    input: str
    name: str
    reference: str
    type: Literal['text_similarity']
