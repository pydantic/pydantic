#!/usr/bin/env python3
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

from packaging.version import parse


def main(env_var='GITHUB_REF') -> int:
    git_ref = os.getenv(env_var, 'none')
    tag = re.sub('^refs/tags/v*', '', git_ref.lower())
    version = SourceFileLoader('version', 'pydantic/version.py').load_module().VERSION.lower()
    if tag == version:
        is_prerelease = parse(version).is_prerelease
        print(
            f'✓ {env_var} env var {git_ref!r} matches package version: {tag!r} == {version!r}, '
            f'is pre-release: {is_prerelease}'
        )
        print(f'::set-output name=IS_PRERELEASE::{json.dumps(is_prerelease)}')
        return 0
    else:
        print(f'✖ {env_var} env var {git_ref!r} does not match package version: {tag!r} != {version!r}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
