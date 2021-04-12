Refactor the whole _pydantic_ `dataclass` decorator to really act like its standard lib equivalent.
It hence keeps `__eq__`, `__hash__`, ... and makes comparison with its non-validated version possible.
It also fixes usage of `frozen` dataclasses in fields and usage of `default_factory` in nested dataclasses.
