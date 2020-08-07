from dateutil.parser import parse as datetime_parse
from validx import Datetime, Dict, Float, Int, List, Str, __version__, exc


class TestValidx:
    package = 'validx'
    version = __version__

    def __init__(self, allow_extra):

        Model = Dict(
            {
                'id': Int(),
                'client_name': Str(maxlen=255),
                'sort_index': Float(),
                'client_phone': Str(maxlen=255, nullable=True),
                'location': Dict(
                    {
                        'latitude': Float(nullable=True),
                        'longitude': Float(nullable=True),
                    },
                    optional=['latitude', 'longitude'],
                    nullable=True,
                ),
                'contractor': Int(min=0, coerce=True, nullable=True),
                'upstream_http_referrer': Str(maxlen=1023, nullable=True),
                'grecaptcha_response': Str(minlen=20, maxlen=1000),
                'last_updated': Datetime(
                    nullable=True,
                    parser=datetime_parse,
                ),
                'skills': List(
                    Dict(
                        {
                            'subject': Str(),
                            'subject_id': Int(),
                            'category': Str(),
                            'qual_level': Str(),
                            'qual_level_id': Int(),
                            'qual_level_ranking': Float(),
                        },
                        defaults={
                            'qual_level_ranking': 0,
                        },
                        optional=['quad_level_ranking'],
                    ),
                ),
            },
            optional=[
                'client_phone',
                'location',
                'contractor',
                'upstream_http_referrer',
                'last_updated',
            ],
        )
        self.allow_extra = allow_extra  # not used
        self.schema = Model

    def validate(self, data):
        try:
            self.schema(data)
            return True, data
        except exc.ValidationError as e:
            return False, str(e)
