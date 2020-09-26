from pydantic import validate_arguments


@validate_arguments
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)

b = repeat.raw_function('good bye', 2, separator=b', ')
print(b)
