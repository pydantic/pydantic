from pydantic import BaseModel, Field


class Model(BaseModel):
    # Required
    undefined_default_no_args: int = Field()
    undefined_default: int = Field(description='my desc')
    positional_ellipsis_default: int = Field(...)
# MYPY: error: Incompatible types in assignment (expression has type "EllipsisType", variable has type "int")  [assignment]
    named_ellipsis_default: int = Field(default=...)
# MYPY: error: Incompatible types in assignment (expression has type "EllipsisType", variable has type "int")  [assignment]

    # Not required
    positional_default: int = Field(1)
    named_default: int = Field(default=2)
    named_default_factory: int = Field(default_factory=lambda: 3)


Model()
# MYPY: error: Missing named argument "undefined_default_no_args" for "Model"  [call-arg]
# MYPY: error: Missing named argument "undefined_default" for "Model"  [call-arg]
# MYPY: error: Missing named argument "positional_ellipsis_default" for "Model"  [call-arg]
# MYPY: error: Missing named argument "named_ellipsis_default" for "Model"  [call-arg]
