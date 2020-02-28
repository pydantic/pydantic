from pydantic import validate_arguments


@validate_arguments
def foo(a: int, *, c: str = 'x') -> str:
    return c * a


# ok
x: str = foo(1, c='hello')
# also ok - because pydantic converts Any to the annotated type
foo('x')
foo(1, c=1)
foo(1, 2)
foo(1, d=2)
# mypy assumes foo is just a function
callable(foo)


@validate_arguments
def bar() -> str:
    return 'x'


# return type should be a string
y: int = bar()
