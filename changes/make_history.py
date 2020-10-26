#!/usr/bin/env python3
import re
import sys
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path

THIS_DIR = Path(__file__).parent
name_regex = re.compile(r'(\d+)-(.*?)\.md')
bullet_list = []

for p in THIS_DIR.glob('*.md'):
    if p.name == 'README.md':
        continue
    m = name_regex.fullmatch(p.name)
    if not m:
        raise RuntimeError(f'{p.name!r}: invalid change file name')
    gh_id, creator = m.groups()
    content = p.read_text().replace('\r\n', '\n').strip('\n. ')
    if '\n\n' in content:
        raise RuntimeError(f'{p.name!r}: content includes multiple paragraphs')
    content = content.replace('\n', '\n  ')
    priority = 0
    if '**breaking change' in content.lower():
        priority = 2
    elif content.startswith('**'):
        priority = 1
    bullet_list.append((priority, int(gh_id), f'* {content}, #{gh_id} by @{creator}'))

if not bullet_list:
    print('no changes found')
    sys.exit(0)

version = SourceFileLoader('version', 'pydantic/version.py').load_module()
chunk_title = f'v{version.VERSION} ({date.today():%Y-%m-%d})'
new_chunk = '## {}\n\n{}\n\n'.format(chunk_title, '\n'.join(c for *_, c in sorted(bullet_list, reverse=True)))

print(f'{chunk_title}...{len(bullet_list)} items')
history_path = THIS_DIR / '..' / 'HISTORY.md'
history = new_chunk + history_path.read_text()

history_path.write_text(history)
for p in THIS_DIR.glob('*.md'):
    if p.name != 'README.md':
        p.unlink()

print(
    'changes deleted and HISTORY.md successfully updated, to reset use:\n\n'
    '  git checkout -- changes/*-*.md HISTORY.md\n'
)
