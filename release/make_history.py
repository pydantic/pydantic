from __future__ import annotations as _annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests


def main():
    root_dir = Path(__file__).parent.parent
    version_file = root_dir / 'pydantic' / 'version.py'

    new_version = re.search(r"VERSION = '(.*)'", version_file.read_text()).group(1)

    history_path = root_dir / 'HISTORY.md'
    history_content = history_path.read_text()

    if f'## v{new_version}' in history_content:
        print(f'WARNING: v{new_version} already in history, stopping')
        sys.exit(1)

    commits = get_commits()
    commits_bullets = '\n'.join(f'* {c}' for c in commits)

    title = f'v{new_version} ({date.today():%Y-%m-%d})'
    new_chunk = (
        f'## {title}\n\n'
        f'[GitHub release](https://github.com/pydantic/pydantic/releases/tag/v{new_version})\n\n'
        f'{commits_bullets}\n\n'
    )
    history = new_chunk + history_content

    history_path.write_text(history)
    print(f'\nSUCCESS: added "{title}" section to {history_path.relative_to(root_dir)}')


def get_commits() -> list[Commit]:
    last_tag = get_last_tag()
    raw_commits = run('git', 'log', f'{last_tag}..main', '--oneline')
    commits = [Commit.from_line(line) for line in raw_commits.splitlines()]
    commits = [c for c in commits if c]
    print(f'found {len(commits)} commits since {last_tag}')
    add_author(commits)
    return commits


@dataclass
class Commit:
    short_sha: str
    message: str
    pr: int
    author: str | None = None

    @classmethod
    def from_line(cls, line: str) -> Commit | None:
        short_sha, message = line.split(' ', 1)
        message, last_word = message.rsplit(' ', 1)
        m = re.fullmatch(r'\(#(\d+)\)', last_word)
        if m:
            pr = int(m.group(1))
            return cls(short_sha, message, pr)

    def __str__(self):
        return f'{self.message} by @{self.author} in [#{self.pr}](https://github.com/pydantic/pydantic/pull/{self.pr})'


def add_author(commits: list[Commit]) -> None:
    print('Getting PR authors from GitHub...')
    session = requests.Session()
    headers = {
        'Accept': 'application/vnd.github+json',
        'x-github-api-version': '2022-11-28',
    }
    missing = {c.pr for c in commits}
    for page in range(1, 10):
        print(f'getting GH pulls page {page}, looking for {len(missing)} missing authors...')
        params = {'per_page': 100, 'page': page, 'direction': 'desc', 'sort': 'updated', 'state': 'closed'}
        r = session.get('https://api.github.com/repos/pydantic/pydantic/pulls', headers=headers, params=params)
        r.raise_for_status()
        for pr in r.json():
            pr_number = pr['number']
            # debug(pr_number, missing, pr_number in missing)
            if pr_number in missing:
                for c in commits:
                    if c.pr == pr_number:
                        missing.remove(pr_number)
                        c.author = pr['user']['login']
                        break
        if not missing:
            print(f'all authors found after page {page}')
            return
        else:
            print(f'{len(missing)} authors still missing after page {page}')


def get_last_tag():
    return run('git', 'describe', '--tags', '--abbrev=0')


def run(*args: str) -> str:
    p = subprocess.run(args, stdout=subprocess.PIPE, check=True, encoding='utf-8')
    return p.stdout.strip()


if __name__ == '__main__':
    main()
