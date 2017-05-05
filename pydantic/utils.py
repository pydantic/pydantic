import re
from importlib import import_module


def _rfc_1738_quote(text):
    return re.sub(r'[:@/]', lambda m: '%{:X}'.format(ord(m.group(0))), text)


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


def import_string(dotted_path):
    """
    Stolen approximately from django. Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.strip(' ').rsplit('.', 1)
    except ValueError as e:
        raise ImportError("{} doesn't look like a module path".format(dotted_path)) from e

    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError('Module "{}" does not define a "{}" attribute'.format(module_path, class_name)) from e
