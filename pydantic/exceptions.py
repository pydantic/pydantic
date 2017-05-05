import json


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        e_count = len(errors)
        s = '' if e_count == 1 else 's'
        self.message = f'{e_count} error{s} validating input'
        self.pretty_errors = json.dumps(errors, sort_keys=True)
        super().__init__(f'{self.message}: {self.pretty_errors}')


class ConfigError(RuntimeError):
    pass
