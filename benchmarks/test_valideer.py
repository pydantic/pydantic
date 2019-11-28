import re
import subprocess

import dateutil.parser
import valideer as V

# valideer appears to provide no way of getting the installed version
p = subprocess.run(['pip', 'freeze'], stdout=subprocess.PIPE, encoding='utf8', check=True)
valideer_version = re.search(r'valideer==(.+)', p.stdout).group(1)


class TestValideer:
    package = 'valideer'
    version = valideer_version

    def __init__(self, allow_extra):
        schema = {
            '+id': int,
            '+client_name': V.String(max_length=255),
            '+sort_index': float,
            'client_phone': V.Nullable(V.String(max_length=255)),
            'location': {'latitude': float, 'longitude': float},
            'contractor': V.Range(V.AdaptTo(int), min_value=1),
            'upstream_http_referrer': V.Nullable(V.String(max_length=1023)),
            '+grecaptcha_response': V.String(min_length=20, max_length=1000),
            'last_updated': V.AdaptBy(dateutil.parser.parse),
            'skills': V.Nullable(
                [
                    {
                        '+subject': str,
                        '+subject_id': int,
                        '+category': str,
                        '+qual_level': str,
                        '+qual_level_id': int,
                        'qual_level_ranking': V.Nullable(float, default=0),
                    }
                ],
                default=[],
            ),
        }
        self.validator = V.parse(schema, additional_properties=allow_extra)

    def validate(self, data):
        try:
            return True, self.validator.validate(data)
        except V.ValidationError as e:
            return False, str(e)
