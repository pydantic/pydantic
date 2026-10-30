
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ._utils import is_list as is_list, lru_cache as lru_cache, is_mapping as is_mapping, coerce_boolean as coerce_boolean, strip_not_given as strip_not_given
from ._compat import get_args as get_args, is_union as is_union, get_origin as get_origin, is_literal_type as is_literal_type
from ._typing import extract_type_arg as extract_type_arg, is_annotated_type as is_annotated_type, is_type_alias_type as is_type_alias_type, strip_annotated_type as strip_annotated_type
from ._transform import PropertyInfo as PropertyInfo
from ._datetime_parse import parse_date as parse_date, parse_datetime as parse_datetime
