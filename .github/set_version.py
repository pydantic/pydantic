#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path


def main(cargo_path_env_var='CARGO_PATH', version_env_vars=('VERSION', 'GITHUB_REF')) -> int:
    cargo_path = os.getenv(cargo_path_env_var, 'Cargo.toml')
    cargo_path = Path(cargo_path)
    if not cargo_path.is_file():
        print(f'✖ path "{cargo_path}" does not exist')
        return 1

    version = None
    for var in version_env_vars:
        version_ref = os.getenv(var)
        if version_ref:
            version = re.sub('^refs/tags/v*', '', version_ref.lower())
            break
    if not version:
        print(f'✖ "{version_env_vars}" env variables not found')
        return 1

    # convert from python pre-release version to rust pre-release version
    # this is the reverse of what's done in lib.rs::_rust_notify
    version = version.replace('a', '-alpha').replace('b', '-beta')
    print(f'writing version "{version}", to {cargo_path}')

    version_regex = re.compile('^version ?= ?".*"', re.M)
    cargo_content = cargo_path.read_text()
    if not version_regex.search(cargo_content):
        print(f'✖ {version_regex!r} not found in {cargo_path}')
        return 1

    new_content = version_regex.sub(f'version = "{version}"', cargo_content)
    cargo_path.write_text(new_content)
    return 0


if __name__ == '__main__':
    sys.exit(main())
