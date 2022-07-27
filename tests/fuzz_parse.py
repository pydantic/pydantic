import sys

import atheris

from pydantic.parse import Protocol, load_str_bytes


def TestOneInput(data):
    try:
        _ = load_str_bytes(b=data, proto=Protocol.json)
    except ValueError:
        None


def main():
    atheris.instrument_all()
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
