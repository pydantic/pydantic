from datetime import datetime
from typing import List

from runtype import __version__, dataclass, String, Int


class TestRuntype:
    package = 'runtype'
    version = __version__

    def __init__(self, allow_extra):
        @dataclass(check_types='cast')
        class Model:
            id: int
            client_name: String(max_length=255)
            sort_index: float
            # client_email: EmailStr = None
            client_phone: String(max_length=255) = None

            @dataclass
            class Location:
                latitude: float = None
                longitude: float = None

            location: Location = None

            contractor: Int(min=0) = None
            upstream_http_referrer: String(max_length=1023) = None
            grecaptcha_response: String(min_length=20, max_length=1000)
            last_updated: datetime = None

            @dataclass
            class Skill:
                subject: str
                subject_id: int
                category: str
                qual_level: str
                qual_level_id: int
                qual_level_ranking: float = 0

            skills: List[Skill] = []

            class Config:
                extra: dict = dict

        self.model = Model

    def validate(self, data):
        try:
            return True, self.model(**data)
        except TypeError as e:
            return False, str(e)

    def to_json(self, model):
        return model.json()
