from pydantic import Secret


def takes_secret(scalar_secret: Secret[str | int | float | bool]) -> None: ...


def secret_usage() -> None:
    secret: Secret[str] = Secret('my secret')
    takes_secret(secret)
