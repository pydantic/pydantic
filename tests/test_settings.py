from pydantic import BaseSettings


class SimpleSettings(BaseSettings):
    apple: str = ...


def test_sub_env(env):
    env.set('APP_APPLE', 'hello')
    s = SimpleSettings()
    assert s.apple == 'hello'


def test_sub_env_override(env):
    env.set('APP_APPLE', 'hello')
    s = SimpleSettings(apple='goodbye')
    assert s.apple == 'goodbye'
