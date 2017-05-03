from typing import Any, Type


class BaseField:
    def __init__(
            self, *,
            default: Any=None,
            v_type: Type=None,
            required: bool=False,
            description: str=None):
        if default and v_type:
            raise RuntimeError('"default" and "v_type" cannot both be defined.')
        elif default and required:
            raise RuntimeError('It doesn\'t make sense to have "default" set and required=True.')
        if default:
            self.default = default
            self.v_type = type(default)
        else:
            self.v_type = v_type
        self.required = required
        self.description = description


class EnvField(BaseField):
    def __init__(self, *, env=None, **kwargs):
        super().__init__(**kwargs)
        self.env_var_name = env
