# to be removed with PEP 747:
# mypy: disable_error_code=var-annotated
from typing import Annotated

from typing_extensions import assert_type

from pydantic import TypeAdapter

ta1 = TypeAdapter(int)
assert_type(ta1, TypeAdapter[int])

assert_type(ta1.validate_python('1'), int)
ta1.dump_python(1)
ta1.dump_python('1')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
ta1.dump_json(1)
ta1.dump_json('1')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

# The following use cases require PEP 747: TypeExpr:

ta2 = TypeAdapter(Annotated[int, ...])
assert_type(ta2, TypeAdapter[int])  # type: ignore[assert-type]  # pyright: ignore[reportAssertTypeFailure]

ta3: TypeAdapter[int] = TypeAdapter(Annotated[int, ...])
assert_type(ta3, TypeAdapter[int])

ta4 = TypeAdapter(int | str)
assert_type(ta4, TypeAdapter[int | str])  # type: ignore[assert-type]  # pyright: ignore[reportAssertTypeFailure]
