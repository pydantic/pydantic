import toastedmarshmallow
from test_marshmallow import TestMarshmallow


class TestToastedMarshmallow(TestMarshmallow):
    package = 'toasted-marshmallow'

    def __init__(self, allow_extra):
        super().__init__(allow_extra)
        self.schema.jit = toastedmarshmallow.Jit
