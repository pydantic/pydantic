import dataclasses
import importlib
import os
import re
import sys
from bisect import insort
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import pytest

try:
    from mypy import api as mypy_api
    from mypy.version import __version__ as mypy_version

    from pydantic.version import parse_mypy_version

except ImportError:
    mypy_api = None
    mypy_version = None

    parse_mypy_version = lambda _: (0,)  # noqa: E731


MYPY_VERSION_TUPLE = parse_mypy_version(mypy_version)
PYDANTIC_ROOT = Path(__file__).parent.parent.parent

pytestmark = pytest.mark.skipif(
    '--test-mypy' not in sys.argv
    and os.environ.get('PYCHARM_HOSTED') != '1',  # never skip when running via the PyCharm runner
    reason='Test only with "--test-mypy" flag',
)

# This ensures mypy can find the test files, no matter where tests are run from:
os.chdir(Path(__file__).parent.parent.parent)


@dataclasses.dataclass
class MypyCasesBuilder:
    configs: Union[str, List[str]]
    modules: Union[str, List[str]]
    marks: Any = None

    def build(self) -> List[Union[Tuple[str, str], Any]]:
        """
        Produces the cartesian product of the configs and modules, optionally with marks.
        """
        if isinstance(self.configs, str):
            self.configs = [self.configs]
        if isinstance(self.modules, str):
            self.modules = [self.modules]
        built_cases = []
        for config in self.configs:
            for module in self.modules:
                built_cases.append((config, module))
        if self.marks is not None:
            built_cases = [pytest.param(config, module, marks=self.marks) for config, module in built_cases]
        return built_cases


cases = (
    # No plugin
    MypyCasesBuilder(
        ['mypy-default.ini', 'pyproject-default.toml'],
        ['fail1.py', 'fail2.py', 'fail3.py', 'fail4.py', 'pydantic_settings.py'],
    ).build()
    + MypyCasesBuilder(
        ['mypy-default.ini', 'pyproject-default.toml'],
        'success.py',
        pytest.mark.skipif(MYPY_VERSION_TUPLE > (1, 0, 1), reason='Need to handle some more things for mypy >=1.1.1'),
    ).build()
    + MypyCasesBuilder(
        ['mypy-default.ini', 'pyproject-default.toml'],
        'root_models.py',
        pytest.mark.skipif(
            MYPY_VERSION_TUPLE < (1, 1, 1), reason='`dataclass_transform` only supported on mypy >= 1.1.1'
        ),
    ).build()
    + MypyCasesBuilder(
        'mypy-default.ini', ['plugin_success.py', 'plugin_success_baseConfig.py', 'metaclass_args.py']
    ).build()
    # Default plugin config
    + MypyCasesBuilder(
        ['mypy-plugin.ini', 'pyproject-plugin.toml'],
        [
            'plugin_success.py',
            'plugin_fail.py',
            'plugin_success_baseConfig.py',
            'plugin_fail_baseConfig.py',
            'pydantic_settings.py',
        ],
    ).build()
    # Strict plugin config
    + MypyCasesBuilder(
        ['mypy-plugin-strict.ini', 'pyproject-plugin-strict.toml'],
        [
            'plugin_success.py',
            'plugin_fail.py',
            'fail_defaults.py',
            'plugin_success_baseConfig.py',
            'plugin_fail_baseConfig.py',
        ],
    ).build()
    # One-off cases
    + [
        ('mypy-plugin.ini', 'custom_constructor.py'),
        ('mypy-plugin.ini', 'generics.py'),
        ('mypy-plugin.ini', 'root_models.py'),
        ('mypy-plugin-strict.ini', 'plugin_default_factory.py'),
        ('mypy-plugin-strict-no-any.ini', 'dataclass_no_any.py'),
        ('mypy-plugin-very-strict.ini', 'metaclass_args.py'),
        ('pyproject-default.toml', 'computed_fields.py'),
        ('pyproject-plugin-no-strict-optional.toml', 'no_strict_optional.py'),
    ]
)


@dataclasses.dataclass
class MypyTestTarget:
    parsed_mypy_version: Tuple[int, ...]
    output_path: Path


@dataclasses.dataclass
class MypyTestConfig:
    existing: Optional[MypyTestTarget]  # the oldest target with an output that is no older than the installed mypy
    current: MypyTestTarget  # the target for the current installed mypy


def get_test_config(module_path: Path, config_path: Path) -> MypyTestConfig:
    outputs_dir = PYDANTIC_ROOT / 'tests/mypy/outputs'
    outputs_dir.mkdir(exist_ok=True)
    existing_versions = [
        x.name for x in outputs_dir.iterdir() if x.is_dir() and re.match(r'[0-9]+(?:\.[0-9]+)*', x.name)
    ]

    def _convert_to_output_path(v: str) -> Path:
        return outputs_dir / v / config_path.name.replace('.', '_') / module_path.name

    existing = None

    # Build sorted list of (parsed_version, version) pairs, including the current mypy version being used
    parsed_version_pairs = sorted([(parse_mypy_version(v), v) for v in existing_versions])
    if MYPY_VERSION_TUPLE not in [x[0] for x in parsed_version_pairs]:
        insort(parsed_version_pairs, (MYPY_VERSION_TUPLE, mypy_version))

    for parsed_version, version in parsed_version_pairs[::-1]:
        if parsed_version > MYPY_VERSION_TUPLE:
            continue
        output_path = _convert_to_output_path(version)
        if output_path.exists():
            existing = MypyTestTarget(parsed_version, output_path)
            break

    current = MypyTestTarget(MYPY_VERSION_TUPLE, _convert_to_output_path(mypy_version))
    return MypyTestConfig(existing, current)


@pytest.mark.filterwarnings('ignore:ast.:DeprecationWarning')  # these are produced by mypy in python 3.12
@pytest.mark.parametrize('config_filename,python_filename', cases)
def test_mypy_results(config_filename: str, python_filename: str, request: pytest.FixtureRequest) -> None:
    input_path = PYDANTIC_ROOT / 'tests/mypy/modules' / python_filename
    config_path = PYDANTIC_ROOT / 'tests/mypy/configs' / config_filename
    test_config = get_test_config(input_path, config_path)

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = f'.mypy_cache/test-{os.path.splitext(config_filename)[0]}'
    command = [
        str(input_path),
        '--config-file',
        str(config_path),
        '--cache-dir',
        cache_dir,
        '--show-error-codes',
        '--show-traceback',
    ]
    print(f"\nExecuting: mypy {' '.join(command)}")  # makes it easier to debug as necessary
    mypy_out, mypy_err, mypy_returncode = mypy_api.run(command)

    # Need to strip filenames due to differences in formatting by OS
    mypy_out = '\n'.join(['.py:'.join(line.split('.py:')[1:]) for line in mypy_out.split('\n') if line]).strip()
    mypy_out = re.sub(r'\n\s*\n', r'\n', mypy_out)
    if mypy_out:
        print('{0}\n{1:^100}\n{0}\n{2}\n{0}'.format('=' * 100, f'mypy {mypy_version} output', mypy_out))
    assert mypy_err == ''

    input_code = input_path.read_text()

    existing_output_code: Optional[str] = None
    if test_config.existing is not None:
        existing_output_code = test_config.existing.output_path.read_text()
        print(f'Comparing output with {test_config.existing.output_path}')

    merged_output = merge_python_and_mypy_output(input_code, mypy_out)

    if merged_output == existing_output_code:
        # Test passed, no changes needed
        pass
    elif request.config.getoption('update_mypy'):
        test_config.current.output_path.parent.mkdir(parents=True, exist_ok=True)
        test_config.current.output_path.write_text(merged_output)
    else:
        assert existing_output_code is not None, 'No output file found, run `make test-mypy-update` to create it'
        assert merged_output == existing_output_code
        expected_returncode = get_expected_return_code(existing_output_code)
        assert mypy_returncode == expected_returncode


def test_bad_toml_config() -> None:
    full_config_filename = 'tests/mypy/configs/pyproject-plugin-bad-param.toml'
    full_filename = 'tests/mypy/modules/success.py'

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = '.mypy_cache/test-pyproject-plugin-bad-param'
    command = [full_filename, '--config-file', full_config_filename, '--cache-dir', cache_dir, '--show-error-codes']
    if MYPY_VERSION_TUPLE >= (0, 990):
        command.append('--disable-recursive-aliases')
    print(f"\nExecuting: mypy {' '.join(command)}")  # makes it easier to debug as necessary
    with pytest.raises(ValueError) as e:
        mypy_api.run(command)

    assert str(e.value) == 'Configuration value must be a boolean for key: init_forbid_extra'


def get_expected_return_code(source_code: str) -> int:
    if re.findall(r'^\s*# MYPY:', source_code, flags=re.MULTILINE):
        return 1
    return 0


@pytest.mark.parametrize('module', ['dataclass_no_any', 'plugin_success', 'plugin_success_baseConfig'])
@pytest.mark.filterwarnings('ignore:.*is deprecated.*:DeprecationWarning')
@pytest.mark.filterwarnings('ignore:.*are deprecated.*:DeprecationWarning')
def test_success_cases_run(module: str) -> None:
    """
    Ensure the "success" files can actually be executed
    """
    importlib.import_module(f'tests.mypy.modules.{module}')


def test_explicit_reexports():
    from pydantic import __all__ as root_all
    from pydantic.deprecated.tools import __all__ as tools
    from pydantic.main import __all__ as main
    from pydantic.networks import __all__ as networks
    from pydantic.types import __all__ as types

    for name, export_all in [('main', main), ('network', networks), ('tools', tools), ('types', types)]:
        for export in export_all:
            assert export in root_all, f'{export} is in {name}.__all__ but missing from re-export in __init__.py'


def test_explicit_reexports_exist():
    import pydantic

    for name in pydantic.__all__:
        assert hasattr(pydantic, name), f'{name} is in pydantic.__all__ but missing from pydantic'


@pytest.mark.parametrize(
    'v_str,v_tuple',
    [
        ('0', (0,)),
        ('0.930', (0, 930)),
        ('0.940+dev.04cac4b5d911c4f9529e6ce86a27b44f28846f5d.dirty', (0, 940)),
    ],
)
def test_parse_mypy_version(v_str, v_tuple):
    assert parse_mypy_version(v_str) == v_tuple


def merge_python_and_mypy_output(source_code: str, mypy_output: str) -> str:
    merged_lines = [(line, False) for line in source_code.splitlines()]

    for line in mypy_output.splitlines()[::-1]:
        if not line:
            continue
        try:
            line_number, message = line.split(':', maxsplit=1)
            merged_lines.insert(int(line_number), (f'# MYPY: {message.strip()}', True))
        except ValueError:
            # This could happen due to lack of a ':' in `line`, or the pre-':' contents not being a number
            # Either way, put all such lines at the top of the file
            merged_lines.insert(0, (f'# MYPY: {line.strip()}', True))

    merged_lines = [line for line, is_mypy in merged_lines if is_mypy or not line.strip().startswith('# MYPY: ')]
    return '\n'.join(merged_lines) + '\n'
