from datetime import datetime
from typing import List

from pydantic import VERSION, BaseModel, Extra, PositiveInt, ValidationError, constr


class TestPydantic:
    package = 'pydantic'
    version = str(VERSION)

    def __init__(self, allow_extra):
        class Model(BaseModel):
            id: int
            client_name: constr(max_length=255)
            sort_index: float
            # client_email: EmailStr = None
            client_phone: constr(max_length=255) = None

            class Location(BaseModel):
                latitude: float = None
                longitude: float = None

            location: Location = None

            contractor: PositiveInt = None
            upstream_http_referrer: constr(max_length=1023) = None
            grecaptcha_response: constr(min_length=20, max_length=1000)
            last_updated: datetime = None

            class Skill(BaseModel):
                subject: str
                subject_id: int
                category: str
                qual_level: str
                qual_level_id: int
                qual_level_ranking: float = 0

            skills: List[Skill] = []

            class Config:
                extra = Extra.allow if allow_extra else Extra.forbid

        self.model = Model

    def validate(self, data):
        try:
            return True, self.model(**data)
        except ValidationError as e:
            return False, e.errors()

    def to_json(self, model):
        return model.json()
