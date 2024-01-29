from typing import Union

from pydantic import BaseModel


class MongoSettings(BaseModel):
    MONGO_PASSWORD: Union[str, None]
