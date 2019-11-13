from cerberus import Validator, __version__
from dateutil.parser import parse as datetime_parse


class TestCerberus:
    package = 'cerberus'
    version = str(__version__)

    def __init__(self, allow_extra):
        schema = {
            'id': {'type': 'integer', 'required': True},
            'client_name': {'type': 'string', 'maxlength': 255, 'required': True},
            'sort_index': {'type': 'float', 'required': True},
            'client_phone': {'type': 'string', 'maxlength': 255, 'nullable': True},
            'location': {
                'type': 'dict',
                'schema': {'latitude': {'type': 'float'}, 'longitude': {'type': 'float'}},
                'nullable': True,
            },
            'contractor': {'type': 'integer', 'min': 0, 'nullable': True, 'coerce': int},
            'upstream_http_referrer': {'type': 'string', 'maxlength': 1023, 'nullable': True},
            'grecaptcha_response': {'type': 'string', 'minlength': 20, 'maxlength': 1000, 'required': True},
            'last_updated': {'type': 'datetime', 'nullable': True, 'coerce': datetime_parse},
            'skills': {
                'type': 'list',
                'default': [],
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'subject': {'type': 'string', 'required': True},
                        'subject_id': {'type': 'integer', 'required': True},
                        'category': {'type': 'string', 'required': True},
                        'qual_level': {'type': 'string', 'required': True},
                        'qual_level_id': {'type': 'integer', 'required': True},
                        'qual_level_ranking': {'type': 'float', 'default': 0, 'required': True},
                    },
                },
            },
        }

        self.v = Validator(schema)
        self.v.allow_unknown = allow_extra

    def validate(self, data):
        validated = self.v.validated(data)
        if validated is None:
            return False, self.v.errors
        else:
            return True, validated
