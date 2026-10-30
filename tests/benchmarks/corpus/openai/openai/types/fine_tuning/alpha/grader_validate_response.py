# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import TypeAlias
from ...._models import BaseModel
from ...graders.multi_grader import MultiGrader
from ...graders.python_grader import PythonGrader
from ...graders.score_model_grader import ScoreModelGrader
from ...graders.string_check_grader import StringCheckGrader
from ...graders.text_similarity_grader import TextSimilarityGrader
Grader: TypeAlias = Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, MultiGrader]

class GraderValidateResponse(BaseModel):
    grader: Optional[Grader] = None
