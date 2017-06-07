from pydantic import BaseModel


class UserModel(BaseModel):
    id: int = ...

    class Config:
        min_anystr_length = 0  # min length for str & byte types
        max_anystr_length = 2 ** 16  # max length for str & byte types
        min_number_size = -2 ** 64  # min size for numbers
        max_number_size = 2 ** 64  # max size for numbers
        validate_all = False  # whether or not to validate field defaults
        ignore_extra = True  # whether to ignore any extra values in input data
        allow_extra = False  # whether or not too allow (and include on the model) any extra values in input data
        fields = None  # extra information on each field, currently just "alias is allowed"
