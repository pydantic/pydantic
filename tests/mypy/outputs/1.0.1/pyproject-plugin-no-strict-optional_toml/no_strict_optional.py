from pydantic import BaseModel


class MongoSettings(BaseModel):
    MONGO_PASSWORD: str | None
