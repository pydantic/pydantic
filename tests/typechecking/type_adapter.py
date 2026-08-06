from typing import Annotated, Union

from pydantic_core import MISSING
from typing_extensions import assert_type

from pydantic import TypeAdapter

ta1 = TypeAdapter(int)
assert_type(ta1, TypeAdapter[int])

assert_type(ta1.validate_python('1'), int)
ta1.dump_python(1)
ta1.dump_python('1')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
ta1.dump_json(1)
ta1.dump_json('1')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

# The following use cases are for ensuring `TypeForm` works as expected:

ta2 = TypeAdapter(Annotated[int, ...])
assert_type(ta2, TypeAdapter[int])
assert_type(ta2.validate_python(...), int)

ta3: TypeAdapter[int] = TypeAdapter(Annotated[int, ...])
assert_type(ta3, TypeAdapter[int])
assert_type(ta3.validate_python(...), int)

ta4 = TypeAdapter(int | str)
assert_type(ta4, TypeAdapter[int | str])
assert_type(ta4.validate_python(...), int | str)

ta5 = TypeAdapter(Union[int, str])  # noqa: UP007
assert_type(ta5, TypeAdapter[int | str])
assert_type(ta5.validate_python(...), int | str)

# Mypy doesn't support sentinels mixed with TypeForm:
ta6 = TypeAdapter(MISSING)  # type: ignore[arg-type, var-annotated]
assert_type(ta6, TypeAdapter[MISSING])  # type: ignore[assert-type, valid-type]
assert_type(ta6.validate_python(...), MISSING)  # type: ignore[assert-type, valid-type]
