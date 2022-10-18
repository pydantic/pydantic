#!/usr/bin/env python3
"""
Check the version in Cargo.toml matches the version from `GITHUB_REF` environment variable.
"""
import os
import re
import sys
from pathlib import Path


def main() -> int:
    cargo_path = Path('Cargo.toml')
    if not cargo_path.is_file():
        print(f'✖ path "{cargo_path}" does not exist')
        return 1

    version_ref = os.getenv('GITHUB_REF')
    if version_ref:
        version = re.sub('^refs/tags/v*', '', version_ref.lower())
    else:
        print(f'✖ "GITHUB_REF" env variables not found')
        return 1

    # convert from python pre-release version to rust pre-release version
    # this is the reverse of what's done in lib.rs::_rust_notify
    version = version.replace('a', '-alpha').replace('b', '-beta')

    version_regex = re.compile(r"""^version ?= ?(["'])(.+)\1""", re.M)
    cargo_content = cargo_path.read_text()
    match = version_regex.search(cargo_content)
    if not match:
        print(f'✖ {version_regex!r} not found in {cargo_path}')
        return 1

    cargo_version = match.group(2)
    if cargo_version == version:
        print(f'✓ GITHUB_REF version matches {cargo_path} version "{cargo_version}"')
        return 0
    else:
        print(f'✖ GITHUB_REF version "{version}" does not match {cargo_path} version "{cargo_version}"')
        return 1


if __name__ == '__main__':
    sys.exit(main())
