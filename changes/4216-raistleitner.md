Pydantic didn't support setting fields containing "complex values" like dicts or lists from environment variables using nesting. This PR contains an implementation addressing this issue by checking which field the nested environment variable targets to, checking if the field is a complex value and if so, trying to parse the environment value as a JSON.

This already worked if explicitly using `env=...` keyword arg for a field but not for nested environment variables.
