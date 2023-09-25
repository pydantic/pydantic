from __future__ import annotations as _annotations

import json
import logging
import os
import re
import textwrap
from pathlib import Path
from textwrap import indent

import autoflake  # type: ignore
import pyupgrade._main as pyupgrade_main  # type: ignore
import tomli
from mkdocs.config import Config
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .conversion_table import conversion_table

logger = logging.getLogger('mkdocs.plugin')
THIS_DIR = Path(__file__).parent
DOCS_DIR = THIS_DIR.parent
PROJECT_ROOT = DOCS_DIR.parent


def on_pre_build(config: Config) -> None:
    """
    Before the build starts.
    """
    add_changelog()
    add_mkdocs_run_deps()


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
    markdown = insert_json_output(markdown)
    markdown = remove_code_fence_attributes(markdown)
    if md := render_index(markdown, page):
        return md
    if md := render_why(markdown, page):
        return md
    elif md := build_schema_mappings(markdown, page):
        return md
    elif md := build_conversion_table(markdown, page):
        return md
    elif md := devtools_example(markdown, page):
        return md
    else:
        return markdown


def add_changelog() -> None:
    history = (PROJECT_ROOT / 'HISTORY.md').read_text(encoding='utf-8')
    history = re.sub(r'(\s)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub(r'\[GitHub release]\(', r'[:simple-github: GitHub release](', history)
    history = re.sub('@@', '@', history)
    new_file = DOCS_DIR / 'changelog.md'

    # avoid writing file unless the content has changed to avoid infinite build loop
    if not new_file.is_file() or new_file.read_text(encoding='utf-8') != history:
        new_file.write_text(history, encoding='utf-8')


def add_mkdocs_run_deps() -> None:
    # set the pydantic and pydantic-core versions to configure for running examples in the browser
    pyproject_toml = (PROJECT_ROOT / 'pyproject.toml').read_text()
    pydantic_core_version = re.search(r'pydantic-core==(.+?)["\']', pyproject_toml).group(1)

    version_py = (PROJECT_ROOT / 'pydantic' / 'version.py').read_text()
    pydantic_version = re.search(r'^VERSION ?= (["\'])(.+)\1', version_py, flags=re.M).group(2)

    mkdocs_run_deps = json.dumps([f'pydantic=={pydantic_version}', f'pydantic-core=={pydantic_core_version}'])
    logger.info('Setting mkdocs_run_deps=%s', mkdocs_run_deps)

    html = f"""\
    <script>
    window.mkdocs_run_deps = {mkdocs_run_deps}
    </script>
"""
    path = DOCS_DIR / 'theme/mkdocs_run_deps.html'
    path.write_text(html)


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
        numbers = match.group(3)
        # import devtools
        # devtools.debug(numbers)
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

            content = indent(f'{prefix}\n{tab_code}```{numbers}', ' ' * 4)
            output.append(f'=== "Python 3.{minor_version} and above"\n\n{content}')

        if len(output) == 1:
            return match.group(0)
        else:
            return '\n\n'.join(output)

    return re.sub(r'^(``` *py.*?)\n(.+?)^```(\s+(?:^\d+\. .+?\n)+)', add_tabs, markdown, flags=re.M | re.S)


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


def insert_json_output(markdown: str) -> str:
    """
    Find `output="json"` code fence tags and replace with a separate JSON section
    """

    def replace_json(m: re.Match[str]) -> str:
        start, attrs, code = m.groups()

        def replace_last_print(m2: re.Match[str]) -> str:
            ind, json_text = m2.groups()
            json_text = indent(json.dumps(json.loads(json_text), indent=2), ind)
            # no trailing fence as that's not part of code
            return f'\n{ind}```\n\n{ind}JSON output:\n\n{ind}```json\n{json_text}\n'

        code = re.sub(r'\n( *)"""(.*?)\1"""\n$', replace_last_print, code, flags=re.S)
        return f'{start}{attrs}{code}{start}\n'

    return re.sub(r'(^ *```)([^\n]*?output="json"[^\n]*?\n)(.+?)\1', replace_json, markdown, flags=re.M | re.S)


def remove_code_fence_attributes(markdown: str) -> str:
    """
    There's no way to add attributes to code fences that works with both pycharm and mkdocs, hence we use
    `py key="value"` to provide attributes to pytest-examples, then remove those attributes here.

    https://youtrack.jetbrains.com/issue/IDEA-297873 & https://python-markdown.github.io/extensions/fenced_code_blocks/
    """

    def remove_attrs(match: re.Match[str]) -> str:
        suffix = re.sub(
            r' (?:test|lint|upgrade|group|requires|output|rewrite_assert)=".+?"', '', match.group(2), flags=re.M
        )
        return f'{match.group(1)}{suffix}'

    return re.sub(r'^( *``` *py)(.*)', remove_attrs, markdown, flags=re.M)


def get_orgs_data() -> list[dict[str, str]]:
    with (THIS_DIR / 'orgs.toml').open('rb') as f:
        orgs_data = tomli.load(f)
    return orgs_data['orgs']


tile_template = """
<div class="tile">
  <a href="why/#org-{key}" title="{name}">
    <img src="logos/{key}_logo.png" alt="{name}" />
  </a>
</div>"""


def render_index(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'index.md':
        return None

    if version := os.getenv('PYDANTIC_VERSION'):
        url = f'https://github.com/pydantic/pydantic/releases/tag/{version}'
        version_str = f'Documentation for version: [{version}]({url})'
    elif (version_ref := os.getenv('GITHUB_REF')) and version_ref.startswith('refs/tags/'):
        version = re.sub('^refs/tags/', '', version_ref.lower())
        url = f'https://github.com/pydantic/pydantic/releases/tag/{version}'
        version_str = f'Documentation for version: [{version}]({url})'
    elif sha := os.getenv('GITHUB_SHA'):
        url = f'https://github.com/pydantic/pydantic/commit/{sha}'
        sha = sha[:7]
        version_str = f'Documentation for development version: [{sha}]({url})'
    else:
        version_str = 'Documentation for development version'
    logger.info('Setting version prefix: %r', version_str)
    markdown = re.sub(r'{{ *version *}}', version_str, markdown)

    elements = [tile_template.format(**org) for org in get_orgs_data()]

    orgs_grid = f'<div id="grid-container"><div id="company-grid" class="grid">{"".join(elements)}</div></div>'
    return re.sub(r'{{ *organisations *}}', orgs_grid, markdown)


def render_why(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'why.md':
        return None

    with (THIS_DIR / 'using.toml').open('rb') as f:
        using = tomli.load(f)['libs']

    libraries = '\n'.join('* [`{repo}`](https://github.com/{repo}) {stars:,} stars'.format(**lib) for lib in using)
    markdown = re.sub(r'{{ *libraries *}}', libraries, markdown)
    default_description = '_(Based on the criteria described above)_'

    elements = [
        f'### {org["name"]} {{#org-{org["key"]}}}\n\n{org.get("description") or default_description}'
        for org in get_orgs_data()
    ]
    return re.sub(r'{{ *organisations *}}', '\n\n'.join(elements), markdown)


def _generate_table_row(col_values: list[str]) -> str:
    return f'| {" | ".join(col_values)} |\n'


def _generate_table_heading(col_names: list[str]) -> str:
    return _generate_table_row(col_names) + _generate_table_row(['-'] * len(col_names))


def build_schema_mappings(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'usage/schema.md':
        return None

    col_names = [
        'Python type',
        'JSON Schema Type',
        'Additional JSON Schema',
        'Defined in',
        'Notes',
    ]
    table_text = _generate_table_heading(col_names)

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
        cols = [f'`{py_type}`', f'`{json_type}`', f'`{additional}`' if additional else '', defined_in, notes]
        table_text += _generate_table_row(cols)

    return re.sub(r'{{ *schema_mappings_table *}}', table_text, markdown)


def build_conversion_table(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'usage/conversion_table.md':
        return None

    filtered_table_predicates = {
        'all': lambda r: True,
        'json': lambda r: r.json_input,
        'json_strict': lambda r: r.json_input and r.strict,
        'python': lambda r: r.python_input,
        'python_strict': lambda r: r.python_input and r.strict,
    }

    for table_id, predicate in filtered_table_predicates.items():
        table_markdown = conversion_table.filtered(predicate).as_markdown()
        table_markdown = textwrap.indent(table_markdown, '    ')
        markdown = re.sub(rf'{{{{ *conversion_table_{table_id} *}}}}', table_markdown, markdown)

    return markdown


def devtools_example(markdown: str, page: Page) -> str | None:
    if page.file.src_uri != 'integrations/devtools.md':
        return None

    html = (THIS_DIR / 'devtools_output.html').read_text().strip('\n')
    full_html = f'<div class="highlight">\n<pre><code>{html}</code></pre>\n</div>'
    return re.sub(r'{{ *devtools_example *}}', full_html, markdown)
