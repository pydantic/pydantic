from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from git.repo import Repo

if TYPE_CHECKING:
    from git.objects.commit import Commit
    from git.refs.tag import TagReference


REPO_URL = 'https://github.com/pydantic/pydantic'


def get_latest_tag(repo: Repo) -> TagReference:
    tags = repo.tags
    if len(tags) == 0:
        sys.exit('no tags found')

    return tags[-1]


def get_new_commits(repo: Repo) -> list[Commit]:
    latest_tag = get_latest_tag(repo)

    new_commits = []
    commits = repo.iter_commits()
    for commit in commits:
        if commit == latest_tag.commit:
            break

        new_commits.append(commit)

    if len(new_commits) == 0:
        sys.exit('no new commits found')

    return new_commits


def get_latest_package_version(root_dir: Path) -> str:
    version_file = root_dir.joinpath('pydantic', 'version.py')
    latest_version = re.search(r"VERSION = '(.*)'", version_file.read_text())
    if latest_version is None:
        sys.exit('no version found')

    return latest_version.group(1)


def main() -> None:
    root_dir = Path(__file__).parent.parent
    repo = Repo(root_dir)

    filename = 'HISTORY.md'
    history_path = root_dir.joinpath(filename)
    history_content = history_path.read_text()

    new_version = get_latest_package_version(root_dir)
    if f'## v{new_version}' in history_content:
        sys.exit('version already exists')

    bullets = ''

    commits = get_new_commits(repo)
    for commit in commits:
        short_message = str(commit.message).split('\n')[0]
        bullets += f'* {short_message} by @{commit.author.name}\n'

    title = f'{new_version} ({datetime.datetime.now(tz=datetime.timezone.utc).date()})'
    release_url = f'[GitHub Release]({REPO_URL}/releases/tag/v{new_version})'

    new_chunk = f"""## {title}\n\n{release_url}\n\n{bullets}\n"""
    new_history = new_chunk + history_content
    history_path.write_text(new_history)


if __name__ == '__main__':
    main()
