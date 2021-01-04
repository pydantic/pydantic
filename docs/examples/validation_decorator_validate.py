from pydantic import validate_arguments, ValidationError


@validate_arguments
def slow_sum(a: int, b: int) -> int:
    print(f'Called with a={a}, b={b}')
    return a + b


slow_sum(1, 1)

slow_sum.validate(2, 2)

try:
    slow_sum.validate(1, 'b')
except ValidationError as exc:
    print(exc)
