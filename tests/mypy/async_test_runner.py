import asyncio
import os
from typing import Callable, Coroutine, Dict
from unittest import TestCase

import pytest


def collect_marks(test_case):
    def skip_if(fn):
        return fn

    parametrized = False
    argnames = argvalues = ()
    for mark in getattr(test_case, 'pytestmark', []):
        if mark.name == 'parametrize':
            if parametrized:
                raise RuntimeError('Cannot parametrize same function more than once')
            parametrized = True
            argnames, argvalues, *unsupported_args = (*mark.args, *mark.kwargs.values())
            if unsupported_args:
                raise ValueError('Only argnames and argvalues are implemented')
            if isinstance(argnames, str):
                argnames = argnames.split(',')
        elif mark.name == 'skipif':
            skip_if = pytest.mark.skipif(*mark.args, **mark.kwargs)  # noqa (F811 redefinition of unused 'skip_if')
        else:
            raise ValueError(f'@pytest.mark.{mark.name} is unsupported')

    if not parametrized:
        raise RuntimeError("Won't run one and only test case async, sorry...")

    return argnames, argvalues, skip_if


def create_tests(test_case, argnames, argvalues):
    decoys: Dict[str, Callable[['TestCase', str], None]] = {}
    tests_to_run: Dict[str, Callable[[], Coroutine]] = {}
    exceptions: Dict[str, Exception] = {}

    reserved_kwargs = {'__key__', '__parametrize_params__'}
    if reserved_kwargs & set(argnames):
        raise RuntimeError(f'{reserved_kwargs} kwargs are reserved, please change their names')

    for i, values in enumerate(argvalues):
        if len(values) != len(argnames):
            raise ValueError(f'Wrong number of values, expected {len(argnames)}, ' f'got {len(values)}: {i}, {values}')

        parameters = dict(zip(argnames, values))
        parameters_str = f"[{'-'.join(map(str, values))}]"
        parametrized_name = 'test_async' + parameters_str

        def decoy_test_method(_self, key=parametrized_name):
            """
            Set to Test class below, run as a normal TestCase.test_method,

            Raises exception from parametrized_method
            """
            exception = exceptions.get(key)
            if exception is not None:
                # raising another error from exception to show traceback,
                # if you know how to re-raise original error with it's original traceback please rewrite
                raise AssertionError(str(exception)) from exception

        async def parametrized_method(*args, __parametrize_params__=parameters, __key__=parametrized_name, **kwargs):
            """
            Actual test that gonna be executed asynchronously, exception will be raised in decoy_test_method
            """
            try:
                return await test_case(*args, **kwargs, **__parametrize_params__)
            except Exception as e:
                exceptions[__key__] = e.with_traceback(e.__traceback__.tb_next)  # store exc with original traceback

        decoy_test_method.__name__ = decoy_test_method.__qualname__ = parametrized_name
        decoys[parametrized_name] = decoy_test_method
        tests_to_run[parametrized_name] = parametrized_method
    return decoys, tests_to_run


def run_async(test_case):
    """
    Asynchronously run parametrized test cases.

    Supports pytest.mark.skipif, doesn't support any other marks or fixtures (can be implemented if needed)
    """
    if not asyncio.iscoroutinefunction(test_case):
        raise TypeError('run_async supports only async functions')

    argnames, argvalues, skip_if = collect_marks(test_case)
    decoys, tests_to_run = create_tests(test_case, argnames, argvalues)

    async def run_tests():
        async with asyncio.Semaphore(os.cpu_count()):
            await asyncio.wait([asyncio.ensure_future(test()) for test in tests_to_run.values()], timeout=30)

    @skip_if
    class Test(TestCase):
        locals().update(decoys)

        @classmethod
        def setUpClass(cls) -> None:
            """
            All tests run here, result exceptions raised later in decoy methods
            """
            asyncio.get_event_loop().run_until_complete(run_tests())

    Test.__name__ = Test.__qualname__ = test_case.__name__
    return Test
