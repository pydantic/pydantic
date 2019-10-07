from pydantic import BaseModel, StrictBool


class Flags(BaseModel):
    strict_bool: StrictBool = False
