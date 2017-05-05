import json


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(f'{len(self.errors)} errors validating input: {json.dumps(errors, sort_keys=True)}')


class ConfigError(RuntimeError):
    pass
