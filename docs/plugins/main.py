import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import rtoml
from ansi2html import Ansi2HTMLConverter
from mkdocs.config import Config
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

logger = logging.getLogger('mkdocs.plugin')
THIS_DIR = Path(__file__).parent
DOCS_DIR = THIS_DIR.parent
PROJECT_ROOT = DOCS_DIR.parent


def on_pre_build(config: Config) -> None:
    """
    Before the build starts.
    """
    add_changelog()


def on_files(files: Files, config: Config) -> Files:
    """
    After the files are loaded, but before they are read.
    """
    remove_files(files)
    return files


def on_page_markdown(markdown: str, page: Page, config: Config, files: Files) -> str:
    """
    Called on each file after it is read and before it is converted to HTML.
    """
    if md := add_version(markdown, page):
        return md
    elif md := build_schema_mappings(markdown, page):
        return md
    elif md := devtools_example(markdown, page):
        return md
    else:
        return markdown


def add_changelog() -> None:
    history = (PROJECT_ROOT / 'HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/pydantic/pydantic/issues/\1)', history)
    history = re.sub(r'(\s)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)
    new_file = DOCS_DIR / 'changelog.md'

    # avoid writing file unless the content has changed to avoid infinite build loop
    if not new_file.is_file() or new_file.read_text() != history:
        new_file.write_text(history)


def remove_files(files: Files) -> None:
    to_remove = []
    for file in files:
        if file.src_path.startswith('__pycache__/'):
            to_remove.append(file)

    logger.debug('removing files: %s', [f.src_path for f in to_remove])
    for f in to_remove:
        files.remove(f)


def add_version(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'index.md':
        return None

    version_ref = os.getenv('GITHUB_REF')
    if version_ref:
        version = re.sub('^refs/tags/', '', version_ref.lower())
        version_str = f'Documentation for version: **{version}**'
    else:
        version_str = 'Documentation for development version'
    markdown = re.sub(r'{{ *version *}}', version_str, markdown)
    return markdown


headings = [
    'Python type',
    'JSON Schema Type',
    'Additional JSON Schema',
    'Defined in',
]


def md2html(s: str) -> str:
    return re.sub(r'`(.+?)`', r'<code>\1</code>', s)


def build_schema_mappings(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'usage/schema.md':
        return None

    rows = []
    table = rtoml.load(THIS_DIR / 'schema_mappings.toml')
    for t in table.values():
        py_type = t['py_type']
        json_type = t['json_type']
        additional = t['additional']
        defined_in = t['defined_in']
        notes = t['notes']
        if additional and not isinstance(additional, str):
            additional = json.dumps(additional)
        cols = [
            f'<code>{py_type}</code>',
            f'<code>{json_type}</code>',
            f'<code>{additional}</code>' if additional else '',
            md2html(defined_in),
        ]
        rows.append('\n'.join(f'  <td>\n    {c}\n  </td>' for c in cols))
        if notes:
            rows.append(
                f'  <td colspan=4 style="border-top: none; padding-top: 0">\n'
                f'    <em>{md2html(notes)}</em>\n'
                f'  </td>'
            )

    heading = '\n'.join(f'  <th>{h}</th>' for h in headings)
    body = '\n</tr>\n<tr>\n'.join(rows)
    table_text = f"""\
<table style="width:100%">
<thead>
<tr>
{heading}
</tr>
</thead>
<tbody>
<tr>
{body}
</tr>
</tbody>
</table>
"""
    return re.sub(r'{{ *schema_mappings_table *}}', table_text, markdown)


def devtools_example(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'usage/devtools.md':
        return None

    # TODO change to `{.`
    m = re.search(r'^```py.*?\n(.+?)^```', markdown, flags=re.M | re.S)
    assert m, 'devtools example code not found'

    with NamedTemporaryFile(suffix='.py') as f:
        f.write(m.group(1).encode())
        f.flush()
        os.environ['PY_DEVTOOLS_HIGHLIGHT'] = 'true'
        p = subprocess.run((sys.executable, f.name), stdout=subprocess.PIPE, check=True, encoding='utf8')

    conv = Ansi2HTMLConverter()

    # replace ugly file path with "devtools_example.py"
    output = re.sub(r'/.+?\.py', 'devtools_example.py', p.stdout)
    html = conv.convert(output, full=False).strip('\r\n')
    full_html = f'<div class="terminal">\n<pre class="terminal-content">\n{html}\n</pre>\n</div>'
    return re.sub(r'{{ *devtools_example *}}', full_html, markdown)
