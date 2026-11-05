"""Automate the version bump and changelog update process."""

import argparse
import json
import re
import warnings
from datetime import date
from pathlib import Path

import requests

from release.shared import (
    CORE_CARGO_FILE,
    GITHUB_TOKEN,
    HISTORY_FILE,
    PACKAGE_VERSION_FILE,
    PYPROJECT_FILE,
    REPO,
    run_command,
)

ROOT_DIR = Path(__file__).parent.parent

# Leading markdownlint directives (and blank lines) at the top of the history file,
# which should be kept before the new release section:
HISTORY_DIRECTIVES_REGEX = re.compile(r'\A(?:<!--.*-->\n|\n)*')


def update_version(new_version: str, dry_run: bool) -> None:
    """Update the version in the giving py version file."""
    version_file_path = ROOT_DIR / PACKAGE_VERSION_FILE
    content = version_file_path.read_text(encoding='utf-8')

    # Regex to match the VERSION assignment
    pattern = r'(VERSION\s*=\s*[\'\"])([^\"^\']+)([\'\"])'
    version_stm = re.search(pattern, content)
    if not version_stm:
        print(
            'Could not find the version assignment in the version file. '
            "Please make sure the version file has a line like `VERSION: Final = '1.2.3'`."
        )
        raise SystemExit(1)
    old_version = version_stm.group(2)
    if old_version == new_version:
        warnings.warn('The new version is the same as the old version. The script might not have any effect.')
    old_version_stm = ''.join(version_stm.groups())
    new_version_stm = old_version_stm.replace(old_version, new_version)

    if dry_run:
        print(f'Updating version in version file at "{PACKAGE_VERSION_FILE}"')
        print('--- Before ---')
        print(old_version_stm)
        print('--- After ---')
        print(new_version_stm)
        print('Running in dry mode, lock file is not updated.')
        return

    version_file_path.write_text(content.replace(old_version_stm, new_version_stm), encoding='utf-8')
    run_command('uv', 'lock', '-P', 'pydantic')


def _replace_version_in_file(file: str, pattern: str, new_version: str, dry_run: bool) -> None:
    """Replace the version captured by the `version` group of `pattern` (matched once) in `file`."""
    file_path = ROOT_DIR / file
    content = file_path.read_text(encoding='utf-8')

    match = re.search(pattern, content, flags=re.MULTILINE)
    if match is None:
        print(f'Could not find the pydantic-core version in "{file}" (pattern: {pattern!r}).')
        raise SystemExit(1)
    if match.group('version') == new_version:
        warnings.warn(f'The pydantic-core version in "{file}" is already {new_version}.')

    old_stm = match.group(0)
    start, end = match.span('version')
    new_stm = content[match.start() : start] + new_version + content[end : match.end()]

    if dry_run:
        print(f'Updating pydantic-core version in "{file}"')
        print('--- Before ---')
        print(old_stm)
        print('--- After ---')
        print(new_stm)
        return

    file_path.write_text(content[: match.start()] + new_stm + content[match.end() :], encoding='utf-8')


def update_core_version(new_version: str, dry_run: bool) -> None:
    """Update the pydantic-core version, the pydantic-core pin in pydantic and the compatibility check."""
    # The `[package]` table comes first in the Cargo manifest:
    _replace_version_in_file(CORE_CARGO_FILE, r'^version = "(?P<version>[^"]+)"$', new_version, dry_run)
    _replace_version_in_file(PYPROJECT_FILE, r"""['"]pydantic-core==(?P<version>[^'"]+)['"]""", new_version, dry_run)
    _replace_version_in_file(
        PACKAGE_VERSION_FILE,
        r"""^_COMPATIBLE_PYDANTIC_CORE_VERSION\s*=\s*['"](?P<version>[^'"]+)['"]""",
        new_version,
        dry_run,
    )

    if dry_run:
        print('Running in dry mode, lock files are not updated.')
        return

    # Only update the workspace members' entries in the lock file:
    run_command('cargo', 'update', '--workspace', '--offline', '--manifest-path', CORE_CARGO_FILE)
    run_command('uv', 'lock', '-P', 'pydantic', '-P', 'pydantic-core')


def get_notes(new_version: str) -> str:
    """Fetch auto-generated release notes from github."""
    last_tag = run_command('git', 'describe', '--tags', '--abbrev=0', '--match', 'v*')
    auth_token = GITHUB_TOKEN

    data = {'target_committish': 'main', 'previous_tag_name': last_tag, 'tag_name': f'v{new_version}'}
    response = requests.post(
        f'https://api.github.com/repos/{REPO}/releases/generate-notes',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {auth_token}',
            'x-github-api-version': '2022-11-28',
        },
        data=json.dumps(data),
        timeout=100,
    )
    response.raise_for_status()

    body = response.json()['body']
    body = body.replace('<!-- Release notes generated using configuration in .github/release.yml at main -->\n\n', '')

    # Add one level to all headers so they match HISTORY.md, and add trailing newline
    body = re.sub(pattern='^(#+ .+?)$', repl=r'#\1\n', string=body, flags=re.MULTILINE)

    # Ensure a blank line before headers
    body = re.sub(pattern='([^\n])(\n#+ .+?\n)', repl=r'\1\n\2', string=body)

    # Render PR links nicely
    body = re.sub(
        pattern=f'https://github.com/{REPO}/pull/(\\d+)',
        repl=f'[#\\1](https://github.com/{REPO}/pull/\\1)',
        string=body,
    )

    # Remove "full changelog" link
    body = re.sub(
        pattern=r'\*\*Full Changelog\*\*: https://.*$',
        repl='',
        string=body,
    )

    return body.strip()


def update_history(new_version: str, dry_run: bool, force_update: bool) -> None:
    """Generate release notes and prepend them to HISTORY.md."""
    history_path = ROOT_DIR / HISTORY_FILE
    history_content = history_path.read_text(encoding='utf8')

    # use ( to avoid matching beta versions
    if f'## v{new_version} (' in history_content and not force_update:
        warnings.warn(
            f'WARNING: v{new_version} already in history, {HISTORY_FILE} not updated. \n'
            'Use --force or -f to update the history file anyway.'
        )
        return

    date_today_str = f'{date.today():%Y-%m-%d}'
    title = f'v{new_version} ({date_today_str})'
    notes = get_notes(new_version)
    new_chunk = f'## {title}\n\n[GitHub release](https://github.com/{REPO}/releases/tag/v{new_version})\n\n{notes}\n\n'
    if dry_run:
        print(f'Would add the following to {history_path}:\n{new_chunk}')
    directives_end = HISTORY_DIRECTIVES_REGEX.match(history_content).end()  # pyright: ignore[reportOptionalMemberAccess]
    history = history_content[:directives_end] + new_chunk + history_content[directives_end:]

    if not dry_run:
        history_path.write_text(history)
        print(f'\nSUCCESS: added "{title}" section to {history_path.relative_to(ROOT_DIR)}')

    citation_path = ROOT_DIR / 'CITATION.cff'
    citation_text = citation_path.read_text()

    citation_text = re.sub(r'(?<=\nversion: ).*', f'v{new_version}', citation_text)
    citation_text = re.sub(r'(?<=date-released: ).*', date_today_str, citation_text)
    if dry_run:
        print(
            f'Would update version=v{new_version} and date-released={date_today_str} in '
            f'{citation_path.relative_to(ROOT_DIR)}'
        )
        print(f'Updated content:\n{citation_text}')
    else:
        citation_path.write_text(citation_text)
        print(
            f'SUCCESS: updated version=v{new_version} and date-released={date_today_str} '
            f'in {citation_path.relative_to(ROOT_DIR)}'
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # For easier iteration, can generate the release notes without saving
    parser.add_argument('--pydantic-version', required=True, help='New pydantic version number to release.')
    parser.add_argument(
        '--pydantic-core-version',
        help='New pydantic-core version number to release alongside pydantic (optional).',
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        help='print changes to terminal without saving to version file and the history document.',
        action='store_true',
    )
    parser.add_argument(
        '-f',
        '--force',
        help='Force the update of the version and history file.',
        action='store_true',
    )
    args = parser.parse_args()

    version = args.pydantic_version
    core_version = args.pydantic_core_version
    _dry_run = args.dry_run
    _force_update = args.force

    update_version(version, _dry_run)
    if not _dry_run:
        print(f'Updated version to v{version} in the python version file.')

    if core_version is not None:
        update_core_version(core_version, _dry_run)
        if not _dry_run:
            print(f'Updated pydantic-core version to v{core_version}.')

    update_history(version, _dry_run, _force_update)
