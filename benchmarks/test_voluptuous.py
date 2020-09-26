from dateutil.parser import parse as parse_datetime
import voluptuous as v
from voluptuous.humanize import humanize_error


class TestVoluptuous:
    package = 'voluptuous'
    version = v.__version__

    def __init__(self, allow_extra):
        self.schema = v.Schema(
            {
                v.Required('id'): int,
                v.Required('client_name'): v.All(str, v.Length(max=255)),
                v.Required('sort_index'): float,
                # v.Optional('client_email'): v.Maybe(v.Email),
                v.Optional('client_phone'): v.Maybe(v.All(str, v.Length(max=255))),
                v.Optional('location'): v.Maybe(
                    v.Schema(
                        {
                            'latitude': v.Maybe(float),
                            'longitude': v.Maybe(float)
                        },
                        required=True
                    )
                ),
                v.Optional('contractor'): v.Maybe(v.All(v.Coerce(int), v.Range(min=1))),
                v.Optional('upstream_http_referrer'): v.Maybe(v.All(str, v.Length(max=1023))),
                v.Required('grecaptcha_response'): v.All(str, v.Length(min=20, max=1000)),
                v.Optional('last_updated'): v.Maybe(parse_datetime),
                v.Required('skills', default=[]): [
                    v.Schema(
                        {
                            v.Required('subject'): str,
                            v.Required('subject_id'): int,
                            v.Required('category'): str,
                            v.Required('qual_level'): str,
                            v.Required('qual_level_id'): int,
                            v.Required('qual_level_ranking', default=0): float,
                        }
                    )
                ],
            },
            extra=allow_extra,
        )

    def validate(self, data):
        try:
            return True, self.schema(data)
        except v.MultipleInvalid as e:
            return False, humanize_error(data, e)
