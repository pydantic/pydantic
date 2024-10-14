from typing_extensions import assert_type

from pydantic import RootModel

IntRootModel = RootModel[int]

int_root_model = IntRootModel(1)
bad_root_model = IntRootModel('1')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

assert_type(int_root_model.root, int)


class StrRootModel(RootModel[str]):
    pass


str_root_model = StrRootModel(root='a')

assert_type(str_root_model.root, str)
