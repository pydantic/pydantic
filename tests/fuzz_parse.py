import atheris
from pydantic.parse import load_str_bytes, Protocol

def TestOneInput(data):
    try:
        r = load_str_bytes(b=data, proto=Protocol.json)
    except ValueError:
        None


def main():
    atheris.instrument_all()
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
