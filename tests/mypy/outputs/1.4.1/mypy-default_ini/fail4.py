from typing import Any

from pydantic import BaseModel, root_validator, validate_call


@validate_call
def foo(a: int, *, c: str = 'x') -> str:
# MYPY: note: "foo" defined here
    return c * a


# ok
x: str = foo(1, c='hello')
# fails
foo('x')
# MYPY: error: Argument 1 to "foo" has incompatible type "str"; expected "int"  [arg-type]
foo(1, c=1)
# MYPY: error: Argument "c" to "foo" has incompatible type "int"; expected "str"  [arg-type]
foo(1, 2)
# MYPY: error: Too many positional arguments for "foo"  [misc]
# MYPY: error: Argument 2 to "foo" has incompatible type "int"; expected "str"  [arg-type]
foo(1, d=2)
# MYPY: error: Unexpected keyword argument "d" for "foo"  [call-arg]
# mypy assumes foo is just a function
callable(foo.raw_function)
# MYPY: error: "Callable[[int, DefaultNamedArg(str, 'c')], str]" has no attribute "raw_function"  [attr-defined]


@validate_call
def bar() -> str:
    return 'x'


# return type should be a string
y: int = bar()
# MYPY: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]


# Demonstrate type errors for root_validator signatures
class Model(BaseModel):
    @root_validator()
# MYPY: error: All overload variants of "root_validator" require at least one argument  [call-overload]
# MYPY: note: Possible overload variants:
# MYPY: note:     def root_validator(*, skip_on_failure: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
# MYPY: note:     def root_validator(*, pre: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
# MYPY: note:     def root_validator(*, pre: Literal[False], skip_on_failure: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
    @classmethod
    def validate_1(cls, values: Any) -> Any:
        return values

    @root_validator(pre=True, skip_on_failure=True)
# MYPY: error: No overload variant of "root_validator" matches argument types "bool", "bool"  [call-overload]
# MYPY: note: Possible overload variants:
# MYPY: note:     def root_validator(*, skip_on_failure: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
# MYPY: note:     def root_validator(*, pre: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
# MYPY: note:     def root_validator(*, pre: Literal[False], skip_on_failure: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
    @classmethod
    def validate_2(cls, values: Any) -> Any:
        return values

    @root_validator(pre=False)
# MYPY: error: No overload variant of "root_validator" matches argument type "bool"  [call-overload]
# MYPY: note: Possible overload variants:
# MYPY: note:     def root_validator(*, skip_on_failure: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
# MYPY: note:     def root_validator(*, pre: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
# MYPY: note:     def root_validator(*, pre: Literal[False], skip_on_failure: Literal[True], allow_reuse: bool = ...) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType]
    @classmethod
    def validate_3(cls, values: Any) -> Any:
        return values


Model.non_existent_attribute
# MYPY: error: "type[Model]" has no attribute "non_existent_attribute"  [attr-defined]
