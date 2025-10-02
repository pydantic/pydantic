"""Automate the release draft + PR creation process."""

import re
from pathlib import Path
from subprocess import CalledProcessError

import requests

from release.shared import (
    GITHUB_TOKEN,
    HISTORY_FILE,
    REPO,
    run_command,
)

ROOT_DIR = Path(__file__).parent.parent
HISTORY_RELEASE_HEAD_REGEX = r'^## v(\d+\.\d+\.\d+[a-zA-Z0-9]*)\s'


def get_latest_version_from_changelog() -> str:
    """Get the most recently listed version from the changelog."""
    with open(ROOT_DIR / HISTORY_FILE, encoding='utf8') as f:
        for line in f:
            match = re.match(HISTORY_RELEASE_HEAD_REGEX, line)
            if match:
                return match.group(1)
    raise ValueError('Latest version not found in changelog')


def get_latest_release_notes_from_changelog() -> str:
    """Get the release notes for the latest version from the changelog."""
    with open(ROOT_DIR / HISTORY_FILE, encoding='utf8') as f:
        for line in f:
            match = re.match(HISTORY_RELEASE_HEAD_REGEX, line)
            if match:
                break
        else:
            raise ValueError('Latest version not found in changelog')

        release_notes_li: list[str] = []
        for line in f:
            if re.match(HISTORY_RELEASE_HEAD_REGEX, line):
                break
            release_notes_li.append(line)
    return ''.join(release_notes_li)


def commit_and_push_changes(rl_version: str) -> None:
    """Commit and push changes to a new branch."""
    branch_name = f'release/v{rl_version}'
    run_command('git', 'checkout', '-b', branch_name)
    run_command('git', 'add', '-A')
    try:
        run_command('git', 'commit', '-m', f'Bump version to v{rl_version}')
    except CalledProcessError as e:
        print('No changes related to version bump. Are you sure that you have run prepare.py?')
        raise e
    run_command('git', 'push', 'origin', branch_name)


def open_pull_request(rl_version: str):
    """Open a pull request on GitHub."""
    url = f'https://api.github.com/repos/{REPO}/pulls'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {
        'title': f'Release v{rl_version}',
        'head': f'release/v{rl_version}',
        'base': 'main',
        'body': f'Bumping version to v{rl_version}.',
    }
    response = requests.post(url, json=data, headers=headers, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'HTTP error occurred: {e}')
        print(f'Response content: {response.content.decode()}')
        raise e
    return response.json()['html_url']


def create_version_tag(rl_version: str):
    """Create a version tag."""
    run_command('git', 'tag', f'v{rl_version}')
    run_command('git', 'push', 'origin', f'v{rl_version}')


def create_github_release(new_version: str, notes: str):
    """Create a new release on GitHub."""
    url = f'https://api.github.com/repos/{REPO}/releases'

    data = {
        'tag_name': f'v{new_version}',
        'name': f'v{new_version}',
        'body': notes,
        'draft': True,
    }

    response = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github+json',
        },
        json=data,
        timeout=10,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'HTTP error occurred: {e}')
        print(f'Response content: {response.content.decode()}')
        raise e


def create_github_release_draft(rl_version: str, rl_release_notes: str):
    """Create a GitHub release draft."""
    url = f'https://api.github.com/repos/{REPO}/releases'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {
        'tag_name': f'v{rl_version}',
        'name': f'v{rl_version}',
        'body': rl_release_notes,
        'draft': True,
        'prerelease': False,
    }
    response = requests.post(url, json=data, headers=headers, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'HTTP error occurred: {e}')
        print(f'Response content: {response.content.decode()}')
        raise e
    release_url = response.json()['html_url']
    # Publishing happens in the edit page
    edit_url = release_url.replace('/releases/tag/', '/releases/edit/')
    return edit_url


if __name__ == '__main__':
    version = get_latest_version_from_changelog()
    release_notes = get_latest_release_notes_from_changelog()

    commit_and_push_changes(version)
    pr_url = open_pull_request(version)
    print(f'Opened PR: {pr_url}')

    create_version_tag(version)
    draft_url = create_github_release_draft(version, release_notes)
    print(f'Release draft created: {draft_url}')

    print(f'SUCCESS: Completed release process for v{version}')
