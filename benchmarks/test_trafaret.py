from dateutil.parser import parse
import trafaret as t


class TestTrafaret:
    package = 'trafaret'
    version = '.'.join(map(str, t.__VERSION__))

    def __init__(self, allow_extra):
        self.schema = t.Dict({
            'id': t.Int(),
            'client_name': t.String(max_length=255),
            'sort_index': t.Float,
            # t.Key('client_email', optional=True): t.Or(t.Null | t.Email()),
            t.Key('client_phone', optional=True): t.Or(t.Null | t.String(max_length=255)),

            t.Key('location', optional=True): t.Or(t.Null | t.Dict({
                'latitude': t.Or(t.Float | t.Null),
                'longitude': t.Or(t.Float | t.Null),
            })),

            t.Key('contractor', optional=True): t.Or(t.Null | t.Int(gt=0)),
            t.Key('upstream_http_referrer', optional=True): t.Or(t.Null | t.String(max_length=1023)),
            t.Key('grecaptcha_response'): t.String(min_length=20, max_length=1000),

            t.Key('last_updated', optional=True): t.Or(t.Null | t.String >> parse),

            t.Key('skills', default=[]): t.List(t.Dict({
                'subject': t.String,
                'subject_id': t.Int,
                'category': t.String,
                'qual_level': t.String,
                'qual_level_id': t.Int,
                t.Key('qual_level_ranking', default=0): t.Float,
            })),
        })
        if allow_extra:
            self.schema.allow_extra('*')

    def validate(self, data):
        try:
            return True, self.schema.check(data)
        except t.DataError:
            return False, None
        except ValueError:
            return False, None
