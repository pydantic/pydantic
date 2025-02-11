"""Automate the version bump and changelog update process."""

import argparse
import json
import re
import sys
import warnings
from datetime import date
from pathlib import Path

import requests

from release.shared import (
    REPO,
    GITHUB_TOKEN,
    HISTORY_FILE,
    PACKAGE_VERSION_FILE,
    run_command,
)


ROOT_DIR = Path(__file__).parent.parent


def update_version(new_version: str, dry_run: bool) -> None:
    """Update the version in the giving py version file."""
    version_file_path = ROOT_DIR / PACKAGE_VERSION_FILE
    with open(version_file_path, encoding='utf8') as f:
        content = f.read()

    # Regex to match the VERSION assignment
    pattern = r'(VERSION\s*=\s*)([\'\"])([^\"^\']+)([\'\"])'
    version_stm = re.search(pattern, content)
    if not version_stm:
        print(
            'Could not find the version assignment in the version file.'
            'Please make sure the version file has a line like `VERSION = "1.2.3"`.'
        )
        sys.exit(1)
    old_version = version_stm.group(3)
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
    with open(version_file_path, 'w', encoding='utf8') as f:
        new_content = content.replace(old_version_stm, new_version_stm)
        f.write(new_content)
    run_command('uv', 'lock', '-P', 'pydantic')


def get_notes(new_version: str) -> str:
    """Fetch auto-generated release notes from github."""
    last_tag = run_command('git', 'describe', '--tags', '--abbrev=0')
    auth_token = GITHUB_TOKEN

    data = {
        'target_committish': 'main',
        'previous_tag_name': last_tag,
        'tag_name': f'v{new_version}'
    }
    response = requests.post(
        f'https://api.github.com/repos/{REPO}/releases/generate-notes',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {auth_token}',
            'x-github-api-version': '2022-11-28',
        },
        data=json.dumps(data),
        timeout=100
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
    new_chunk = (
        f'## {title}\n\n'
        f'[GitHub release](https://github.com/{REPO}/releases/tag/v{new_version})\n\n'
        f'{notes}\n\n'
    )
    if dry_run:
        print(f"Would add the following to {history_path}:\n{new_chunk}")
    history = new_chunk + history_content

    if not dry_run:
        history_path.write_text(history)
        print(f'\nSUCCESS: added "{title}" section to {history_path.relative_to(ROOT_DIR)}')

    citation_path = ROOT_DIR / 'CITATION.cff'
    citation_text = citation_path.read_text()

    is_release_version = not ('a' in new_version or 'b' in new_version)
    if not is_release_version:
        version_typ = 'alpha' if 'a' in new_version else 'beta'
        warnings.warn(
            f'WARNING: not updating CITATION.cff because version is {version_typ} version {new_version}'
        )
        return
    else:
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
    parser.add_argument('version', help='New version number to release.')
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

    version = args.version
    _dry_run = args.dry_run
    _force_update = args.force

    update_version(version, _dry_run)
    if not _dry_run:
        print(f'Updated version to v{version} in the python version file.')

    update_history(version, _dry_run, _force_update)
