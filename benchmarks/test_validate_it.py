from datetime import datetime
from typing import List

from pydantic import Extra
from validate_it import schema, Options, ValidationError, to_dict


class TestValidateIt:
    package = "validate_it"
    version = "unknown"

    def __init__(self, allow_extra):
        @schema
        class Skill:
            subject: str
            subject_id: int
            category: str
            qual_level: str
            qual_level_id: int
            qual_level_ranking: float = 0

        @schema
        class Location:
            latitude: float = None
            longitude: float = None

        @schema
        class Model:
            id: int
            client_name: str = Options(max_length=255)
            sort_index: float
            # client_email: EmailStr = None

            location: Location = None

            last_updated: datetime
            contractor: int = Options(min_value=0)
            upstream_http_referrer: str = Options(max_length=1023)
            grecaptcha_response: str = Options(min_length=20, max_length=1000)
            client_phone: str = Options(max_length=255, default=None)

            skills: List[Skill] = []

            extra: str = Options(default=Extra.allow if allow_extra else Extra.forbid)

        self.model = Model

    def validate(self, data):
        try:
            return True, self.model(**data)
        except ValidationError as e:
            return False, e

    def to_json(self, model):
        return to_dict(model)
