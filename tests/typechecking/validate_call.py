from typing_extensions import assert_type

from pydantic import validate_call


@validate_call
def foo(a: int, *, c: str = 'x') -> str:
    return c * a


a = foo(1, c='a')
assert_type(a, str)

foo('', c=1)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

# Not possible to type check currently (see https://github.com/pydantic/pydantic/issues/9883):
foo.raw_function(1, c='a')  # type: ignore[attr-defined]  # pyright: ignore[reportFunctionMemberAccess]


# Should work even when not used as a bare decorator:
@validate_call(config={'arbitrary_types_allowed': True})
def bar(a: int) -> int:
    return a


b = bar(1)
assert_type(b, int)
