from pydantic import validate_arguments, ValidationError


@validate_arguments
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)

b = repeat('x', '4', separator=' ')
print(b)

try:
    c = repeat('hello', 'wrong')
except ValidationError as exc:
    print(exc)
