from .main import BaseModel


class BaseSettings(BaseModel):
    """
    Base class for settings, any setting defined on inheriting classes here can be overridden by:

    Setting the appropriate environment variable, eg. to override FOOBAR, `export APP_FOOBAR="whatever"`.
    This is useful in production for secrets you do not wish to save in code and
    also plays nicely with docker(-compose). Settings will attempt to convert environment variables to match the
    type of the value here.

    Or, passing the custom setting as a keyword argument when initialising settings (useful when testing)
    """
    _ENV_PREFIX = 'APP_'

    DB_DATABASE = None
    DB_USER = None
    DB_PASSWORD = None
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_DRIVER = 'postgres'

    def _substitute_environ(self, custom_settings):
        """
        Substitute environment variables into settings.
        """
        d = {}
        for attr_name in dir(self):
            if attr_name.startswith('_') or attr_name.upper() != attr_name:
                continue

            orig_value = getattr(self, attr_name)

            if isinstance(orig_value, Setting):
                is_required = orig_value.required
                default = orig_value.default
                orig_type = orig_value.v_type
                env_var_name = orig_value.env_var_name
            else:
                default = orig_value
                is_required = False
                orig_type = type(orig_value)
                env_var_name = self._ENV_PREFIX + attr_name

            env_var = os.getenv(env_var_name, None)
            d[attr_name] = default

            if env_var is not None:
                if issubclass(orig_type, bool):
                    env_var = env_var.upper() in ('1', 'TRUE')
                elif issubclass(orig_type, int):
                    env_var = int(env_var)
                elif issubclass(orig_type, Path):
                    env_var = Path(env_var)
                elif issubclass(orig_type, bytes):
                    env_var = env_var.encode()
                elif issubclass(orig_type, str) and env_var.startswith('py::'):
                    env_var = self._import_string(env_var[4:])
                elif issubclass(orig_type, (list, tuple, dict)):
                    # TODO more checks and validation
                    env_var = json.loads(env_var)
                d[attr_name] = env_var
            elif is_required and attr_name not in custom_settings:
                raise RuntimeError('The required environment variable "{0}" is currently not set, '
                                   'you\'ll need to set the environment variable with '
                                   '`export {0}="<value>"`'.format(env_var_name))
        return d
