import re
import typing

# Reversed regex inline flag mappings
# https://docs.rs/regex/latest/regex/#grouping-and-flags
# https://github.com/python/cpython/blob/376c734216f54bb0f6676f60d0c771e24efe0824/Lib/re/_parser.py#L55
INLINE_FLAG_MAPPING = {
    re.IGNORECASE: 'i',
    re.MULTILINE: 'm',
    re.DOTALL: 's',
    re.VERBOSE: 'x',
    re.UNICODE: 'u',
    # extended: not supported by rust regex engine
    re.ASCII: 'a',
}

flag_clean_regex = re.compile(rf"^\(\?[{''.join(INLINE_FLAG_MAPPING.values())}]+\)")


def extract_flagged_pattern(pattern: typing.Pattern[str]) -> str:
    """Extract the regex string with embedded flags from a regex object"""
    # Remove embedded flags at the beginning of the pattern, e.g. (?i)
    # these flags are stored in the pattern.flags attribute
    cleaned_pattern = re.sub(flag_clean_regex, '', pattern.pattern)

    flags_str = ''.join(INLINE_FLAG_MAPPING[flag] for flag in INLINE_FLAG_MAPPING if pattern.flags & flag)

    return f'(?{flags_str}){cleaned_pattern}' if flags_str else pattern.pattern
