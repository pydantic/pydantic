from __future__ import annotations

import ast
import re
from functools import partial
from pathlib import Path
from typing import Any

from griffe import Extension, Inspector, ObjectNode, Visitor, get_logger
from griffe import Object as GriffeObject
from pymdownx.slugs import slugify

DOCS_PATH = Path(__file__).parent.parent
slugifier = slugify(case='lower')
logger = get_logger('griffe_docklinks')


def find_heading(content: str, slug: str, file_path: Path) -> tuple[str, int]:
    for m in re.finditer('^#+ (.+)', content, flags=re.M):
        heading = m.group(1)
        h_slug = slugifier(heading, '-')
        if h_slug == slug:
            return heading, m.end()
    raise ValueError(f'heading with slug {slug!r} not found in {file_path}')


def insert_at_top(path: str, api_link: str) -> str:
    rel_file = path.rstrip('/') + '.md'
    file_path = DOCS_PATH / rel_file
    content = file_path.read_text()
    second_heading = re.search('^#+ ', content, flags=re.M)
    assert second_heading, 'unable to find second heading in file'
    first_section = content[: second_heading.start()]

    if f'[{api_link}]' not in first_section:
        logger.debug('inserting API link "%s" at the top of %s', api_link, file_path.relative_to(DOCS_PATH))
        file_path.write_text('??? api "API Documentation"\n' f'    [`{api_link}`][{api_link}]<br>\n\n' f'{content}')

    heading = file_path.stem.replace('_', ' ').title()
    return f'!!! abstract "Usage Documentation"\n    [{heading}](../{rel_file})\n'


def replace_links(m: re.Match[str], *, api_link: str) -> str:
    path_group = m.group(1)
    if '#' not in path_group:
        # no heading id, put the content at the top of the page
        return insert_at_top(path_group, api_link)

    usage_path, slug = path_group.split('#', 1)
    rel_file = usage_path.rstrip('/') + '.md'
    file_path = DOCS_PATH / rel_file
    content = file_path.read_text()
    heading, heading_end = find_heading(content, slug, file_path)

    next_heading = re.search('^#+ ', content[heading_end:], flags=re.M)
    if next_heading:
        next_section = content[heading_end : heading_end + next_heading.start()]
    else:
        next_section = content[heading_end:]

    if f'[{api_link}]' not in next_section:
        logger.debug('inserting API link "%s" into %s', api_link, file_path.relative_to(DOCS_PATH))
        file_path.write_text(
            f'{content[:heading_end]}\n\n'
            '??? api "API Documentation"\n'
            f'    [`{api_link}`][{api_link}]<br>'
            f'{content[heading_end:]}'
        )

    return f'!!! abstract "Usage Documentation"\n    [{heading}](../{rel_file}#{slug})\n'


def update_docstring(obj: GriffeObject) -> str:
    return re.sub(
        r'usage[\- ]docs: ?https://docs\.pydantic\.dev/.+?/(\S+)',
        partial(replace_links, api_link=obj.path),
        obj.docstring.value,
        flags=re.I,
    )


class UpdateDocstringsExtension(Extension):
    def on_instance(
        self, *, node: ast.AST | ObjectNode, obj: GriffeObject, agent: Visitor | Inspector, **kwargs: Any
    ) -> None:
        if not obj.is_alias and obj.docstring is not None:
            obj.docstring.value = update_docstring(obj)
