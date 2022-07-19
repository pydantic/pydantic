Field aliases are compared with None instead of simple `bool(alias)` because an empty string is a valid JSON attribute name.
