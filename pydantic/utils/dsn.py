import re

from .settings import BaseSettings


def _rfc_1738_quote(text):
    return re.sub(r'[:@/]', lambda m: '%{:X}'.format(ord(m.group(0))), text)


def make_settings_dsn(settings: BaseSettings, prefix='DB'):
    kwargs = {
        f: settings.dict['{}_{}'.format(prefix, f.upper())]
        for f in ('name', 'password', 'host', 'port', 'user', 'driver')
    }
    return make_dsn(**kwargs)


def make_dsn(
        driver: str = None,
        user: str = None,
        password: str = None,
        host: str = None,
        port: str = None,
        name: str = None,
        query: str = None):
    """
    Create a DSN from from connection settings.

    Stolen approximately from sqlalchemy/engine/url.py:URL.
    """
    s = driver + '://'
    if user is not None:
        s += _rfc_1738_quote(user)
        if password is not None:
            s += ':' + _rfc_1738_quote(password)
        s += '@'
    if host is not None:
        if ':' in host:
            s += '[{}]'.format(host)
        else:
            s += host
    if port is not None:
        s += ':{}'.format(int(port))
    if name is not None:
        s += '/' + name
    query = query or {}
    if query:
        keys = list(query)
        keys.sort()
        s += '?' + '&'.join('{}={}'.format(k, query[k]) for k in keys)
    return s
