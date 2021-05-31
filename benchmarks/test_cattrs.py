from datetime import datetime
from typing import List, Optional

import attr
import cattr
from dateutil.parser import parse


class TestCAttrs:
    package = 'attrs + cattrs'
    version = attr.__version__

    def __init__(self, allow_extra):
        # cf. https://github.com/Tinche/cattrs/issues/26 why at least structure_str is needed
        def structure_str(s, _):
            if not isinstance(s, str):
                raise ValueError()
            return s

        def structure_int(i, _):
            if not isinstance(i, int):
                raise ValueError()
            return i

        class PositiveInt(int):
            ...

        def structure_posint(i, x):
            i = PositiveInt(i)
            if not isinstance(i, PositiveInt):
                raise ValueError()
            if i <= 0:
                raise ValueError()
            return i

        cattr.register_structure_hook(datetime, lambda isostring, _: parse(isostring))
        cattr.register_structure_hook(str, structure_str)
        cattr.register_structure_hook(int, structure_int)
        cattr.register_structure_hook(PositiveInt, structure_posint)

        def str_len_val(max_len: int, min_len: int = 0, required: bool = False):
            # validate the max len of a string and optionally its min len and whether None is
            # an acceptable value
            def _check_str_len(self, attribute, value):
                if value is None:
                    if required:
                        raise ValueError("")
                    else:
                        return
                if len(value) > max_len:
                    raise ValueError("")
                if min_len and len(value) < min_len:
                    raise ValueError("")

            return _check_str_len

        def pos_int(self, attribute, value):
            # Validate that value is a positive >0 integer; None is allowed
            if value is None:
                return
            if value <= 0:
                raise ValueError("")

        @attr.s(auto_attribs=True, frozen=True, kw_only=True)
        class Skill:
            subject: str
            subject_id: int
            category: str
            qual_level: str
            qual_level_id: int
            qual_level_ranking: float = 0

        @attr.s(auto_attribs=True, frozen=True, kw_only=True)
        class Location:
            latitude: float = None
            longitude: float = None

        @attr.s(auto_attribs=True, frozen=True, kw_only=True)
        class Model:
            id: int
            sort_index: float
            client_name: str = attr.ib(validator=str_len_val(255))
            # client_email: EmailStr = None
            client_phone: Optional[str] = attr.ib(default=None, validator=str_len_val(255))
            location: Optional[Location] = None

            contractor: Optional[PositiveInt]
            upstream_http_referrer: Optional[str] = attr.ib(default=None, validator=str_len_val(1023))
            grecaptcha_response: str = attr.ib(validator=str_len_val(1000, 20, required=True))
            last_updated: Optional[datetime] = None
            skills: List[Skill] = []

        self.model = Model

    def validate(self, data):
        try:
            return True, cattr.structure(data, self.model)
        except (ValueError, TypeError, KeyError) as e:
            return False, str(e)
