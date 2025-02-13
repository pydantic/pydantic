"""This module contains shared variables and functions for the release scripts."""

import subprocess


def run_command(*args: str) -> str:
    """Run a shell command and return the output."""
    p = subprocess.run(args, stdout=subprocess.PIPE, check=True, encoding='utf-8')
    return p.stdout.strip()


REPO = 'pydantic/pydantic'
HISTORY_FILE = 'HISTORY.md'
PACKAGE_VERSION_FILE = 'pydantic/version.py'
GITHUB_TOKEN = run_command('gh', 'auth', 'token')
