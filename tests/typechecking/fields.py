from pydantic import BaseModel, Field, PrivateAttr


# private attributes should be excluded from
# the synthesized `__init__` method:
class ModelWithPrivateAttr(BaseModel):
    _private_field: str = PrivateAttr()


m = ModelWithPrivateAttr()


def new_list() -> list[int]:
    return []


class Model(BaseModel):
    # `default` and `default_factory` are mutually exclusive:
    f1: int = Field(default=1, default_factory=int)  # type: ignore[call-overload]  # pyright: ignore[reportCallIssue]

    # `default` and `default_factory` matches the annotation:
    f2: int = Field(default='1')  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
    f3: int = Field(default_factory=str)  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]

    f4: int = PrivateAttr(default='1')  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
    f5: int = PrivateAttr(default_factory=str)  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]

    f6: list[str] = Field(default_factory=list)
    f7: list[int] = Field(default_factory=new_list)
    f8: list[str] = Field(default_factory=lambda: list())
    f9: dict[str, str] = Field(default_factory=dict)
    f10: int = Field(default_factory=lambda: 123)

    # Note: mypy may require a different error code for `f12` (see https://github.com/python/mypy/issues/17986).
    f11: list[str] = Field(default_factory=new_list)  # type: ignore[arg-type]  # pyright: ignore[reportAssignmentType]
    f12: int = Field(default_factory=list)  # type: ignore[arg-type, assignment, unused-ignore]  # pyright: ignore[reportAssignmentType]

    # Do not error on the ellipsis:
    f13: int = Field(...)

    # Do not error for invalid assignments when validate_default=True
    f14: int = Field(default='1', validate_default=True)
    f15: int = Field(default_factory=str, validate_default=True)
    f16: int = Field(default='1', validate_default=False)  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
    f17: int = Field(default_factory=str, validate_default=False)  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
