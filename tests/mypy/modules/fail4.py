from pydantic import validate_arguments


@validate_arguments
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


@validate_arguments
def bar() -> str:
    return 'x'


# return type should be a string
y: int = bar()


# nested decorator should not produce an error
@validate_arguments(config={'arbitrary_types_allowed': True})
def baz(a: int, *, c: str = 'x') -> str:
    return c * a


# ok
z: str = baz(1, c='hello')
