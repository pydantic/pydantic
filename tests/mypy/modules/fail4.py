from typing import Any

from pydantic import BaseModel, root_validator, validate_call


@validate_call
def foo(a: int, *, c: str = 'x') -> str:
    return c * a


# ok
x: str = foo(1, c='hello')
# fails
foo('x')
foo(1, c=1)
foo(1, 2)
foo(1, d=2)
# mypy assumes foo is just a function
callable(foo.raw_function)


@validate_call
def bar() -> str:
    return 'x'


# return type should be a string
y: int = bar()


# Demonstrate type errors for root_validator signatures
class Model(BaseModel):
    @root_validator()
    @classmethod
    def validate_1(cls, values: Any) -> Any:
        return values

    @root_validator(pre=True, skip_on_failure=True)
    @classmethod
    def validate_2(cls, values: Any) -> Any:
        return values

    @root_validator(pre=False)
    @classmethod
    def validate_3(cls, values: Any) -> Any:
        return values


Model.non_existent_attribute
