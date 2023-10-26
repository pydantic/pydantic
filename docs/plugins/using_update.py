from pathlib import Path
from time import sleep

import requests
import tomli

THIS_DIR = Path(__file__).parent

session = requests.Session()


def update_lib(lib, *, retry=0):
    repo = lib['repo']
    url = f'https://api.github.com/repos/{repo}'
    resp = session.get(url)
    if resp.status_code == 403 and retry < 3:
        print(f'retrying {repo} {retry}')
        sleep(5)
        return update_lib(lib, retry=retry + 1)

    resp.raise_for_status()
    data = resp.json()
    stars = data['watchers_count']
    print(f'{repo}: {stars}')
    lib['stars'] = stars


with (THIS_DIR / 'using.toml').open('rb') as f:
    table = tomli.load(f)

libs = table['libs']
for lib in libs:
    update_lib(lib)

libs.sort(key=lambda lib: lib['stars'], reverse=True)

with (THIS_DIR / 'using.toml').open('w') as f:
    for lib in libs:
        f.write('[[libs]]\nrepo = "{repo}"\nstars = {stars}\n'.format(**lib))
