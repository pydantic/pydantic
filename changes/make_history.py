#!/usr/bin/env python3.7
import re
import sys
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path

THIS_DIR = Path(__file__).parent
name_regex = re.compile(r'(\d+)-(.*?)\.rst')
bullet_list = []

for p in THIS_DIR.glob('*.rst'):
    m = name_regex.fullmatch(p.name)
    if not m:
        raise RuntimeError(f'{p.name!r}: invalid change file name')
    gh_id, creator = m.groups()
    content = p.read_text().strip('\n. ').replace('\r\n', '\n')
    if '\n\n' in content:
        raise RuntimeError(f'{p.name!r}: content includes multiple paragraphs')
    content = content.replace('\n', '\n  ')
    order = 0 if '**breaking change' in content.lower() else 1
    bullet_list.append((order, int(gh_id), f'* {content}, #{gh_id} by @{creator}'))

if not bullet_list:
    print('no changes found')
    sys.exit(0)

version = SourceFileLoader('version', 'pydantic/version.py').load_module()
chunk_title = f'v{version.VERSION} ({date.today():%Y-%m-%d})'
bullets = '\n'.join(c for *_, c in sorted(bullet_list))
new_chunk = f"""
{chunk_title}
{'.' * len(chunk_title)}
{bullets}
"""

print(f'{chunk_title}...{len(bullet_list)} items')
history_path = THIS_DIR / '..' / 'HISTORY.rst'
history = history_path.read_text()
history = re.sub(r'(History\n-------\n)', fr'\1{new_chunk}', history, count=1)
history_path.write_text(history)
for p in THIS_DIR.glob('*.rst'):
    p.unlink()

print(
    'changes deleted and HISTORY.rst successfully updated, to reset use:\n\n'
    '  git checkout -- changes/*.rst HISTORY.rst\n'
)
