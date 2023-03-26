import json
import logging
import os
import re
from pathlib import Path
from textwrap import indent

import autoflake  # type: ignore
import pyupgrade._main as pyupgrade_main  # type: ignore
import tomli
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
    return files


def on_page_markdown(markdown: str, page: Page, config: Config, files: Files) -> str:
    """
    Called on each file after it is read and before it is converted to HTML.
    """
    markdown = upgrade_python(markdown)
    markdown = remove_code_fence_attributes(markdown)
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


MIN_MINOR_VERSION = 7
MAX_MINOR_VERSION = 11


def upgrade_python(markdown: str) -> str:
    """
    Apply pyupgrade to all python code blocks, unless explicitly skipped, create a tab for each version.
    """

    def add_tabs(match: re.Match[str]) -> str:
        prefix = match.group(1)
        if 'upgrade="skip"' in prefix:
            return match.group(0)

        if m := re.search(r'requires="3.(\d+)"', prefix):
            min_minor_version = int(m.group(1))
        else:
            min_minor_version = MIN_MINOR_VERSION

        py_code = match.group(2)
        output = []
        last_code = py_code
        for minor_version in range(min_minor_version, MAX_MINOR_VERSION + 1):
            if minor_version == min_minor_version:
                tab_code = py_code
            else:
                tab_code = _upgrade_code(py_code, minor_version)
                if tab_code == last_code:
                    continue
                last_code = tab_code

            content = indent(f'{prefix}\n{tab_code}```', ' ' * 4)
            output.append(f'=== "Python 3.{minor_version} and above"\n\n{content}')

        if len(output) == 1:
            return match.group(0)
        else:
            return '\n\n'.join(output)

    return re.sub(r'^(``` *py.*?)\n(.+?)^```', add_tabs, markdown, flags=re.M | re.S)


def _upgrade_code(code: str, min_version: int) -> str:
    upgraded = pyupgrade_main._fix_plugins(
        code,
        settings=pyupgrade_main.Settings(
            min_version=(3, min_version),
            keep_percent_format=True,
            keep_mock=False,
            keep_runtime_typing=True,
        ),
    )
    return autoflake.fix_code(upgraded, remove_all_unused_imports=True)


def remove_code_fence_attributes(markdown: str) -> str:
    """
    There's no way to add attributes to code fences that works with both pycharm and mkdocs, hence we use
    `py key="value"` to provide attributes to pytest-examples, then remove those attributes here.

    https://youtrack.jetbrains.com/issue/IDEA-297873 & https://python-markdown.github.io/extensions/fenced_code_blocks/
    """

    def remove_attrs(match: re.Match[str]) -> str:
        suffix = re.sub(r' (?:test|lint|upgrade|group|requires)=".+?"', '', match.group(2), flags=re.M)
        return f'{match.group(1)}{suffix}'

    return re.sub(r'^( *``` *py)(.*)', remove_attrs, markdown, flags=re.M)


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
    with (THIS_DIR / 'schema_mappings.toml').open('rb') as f:
        table = tomli.load(f)

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

    html = (THIS_DIR / 'devtools_output.html').read_text().strip('\n')
    full_html = f'<div class="highlight">\n<pre><code>{html}</code></pre>\n</div>'
    return re.sub(r'{{ *devtools_example *}}', full_html, markdown)
