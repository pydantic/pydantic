import ast
import re
from functools import partial
from pathlib import Path
from typing import Tuple

from griffe.extensions import VisitorExtension
from pymdownx.slugs import slugify

DOCS_PATH = Path(__file__).parent.parent
slugifier = slugify(case='lower')


def find_heading(content: str, slug: str, file_path: Path) -> Tuple[str, int]:
    for m in re.finditer('^#+ (.+)', content, flags=re.M):
        heading = m.group(1)
        h_slug = slugifier(heading, '-')
        if h_slug == slug:
            return heading, m.end()
    raise ValueError(f'heading with slug {slug!r} not found in {file_path}')


def replace_links(m: re.Match, *, python_file_name: str, object_name: str) -> str:
    usage_path, slug = m.groups()
    rel_file = f'{usage_path}.md'
    file_path = DOCS_PATH / rel_file
    content = file_path.read_text()
    heading, heading_end = find_heading(content, slug, file_path)
    api_link = f'pydantic.{python_file_name[:-3]}.{object_name}'

    next_heading = re.search('^#+ ', content[heading_end:], flags=re.M)
    if next_heading:
        next_section = content[heading_end : heading_end + next_heading.start()]
    else:
        next_section = content[heading_end:]

    if f'[{api_link}]' not in next_section:
        print(f'inserting API link "{api_link}" into {file_path.relative_to(DOCS_PATH)}')
        file_path.write_text(
            f'{content[:heading_end]}\n\n'
            '??? api "API Documentation"\n'
            f'    [`{api_link}`][{api_link}]<br>'
            f'{content[heading_end:]}'
        )

    return f'!!! abstract "Usage Documentation"\n    [{heading}](../{rel_file}#{slug})\n'


class Extension(VisitorExtension):
    def visit(self, node: ast.AST) -> None:
        current_object = self.visitor.current
        if current_object and current_object.docstring:
            current_object.docstring.value = re.sub(
                r'usage[\- ]docs: ?https://docs\.pydantic\.dev/.+?/(.+?)/?#(\S+)',
                partial(replace_links, python_file_name=self.visitor.filepath.name, object_name=current_object.name),
                current_object.docstring.value,
                flags=re.I,
            )


# recommended by pawamoy on gitter, but not working

# def update_docstring(obj: GriffeObject, python_file_name: str) -> str:
#     return re.sub(
#         r'usage[\- ]docs: ?https://docs\.pydantic\.dev/.+?/(.+?)/?#(\S+)',
#         partial(replace_links, python_file_name=python_file_name, object_name=obj.name),
#         obj.docstring.value,
#         flags=re.I,
#     )
#
#
# def update_docstrings_recursively(obj: GriffeObject, python_file_name: str) -> None:
#     if obj.docstring:
#         obj.docstring.value = update_docstring(obj, python_file_name)
#     for member in obj.members.values():
#         update_docstrings_recursively(member, python_file_name)
#
#
# class Extension(VisitorExtension):
#     def visit_module(self, node: ast.AST) -> None:
#         module = self.visitor.current.module
#         update_docstrings_recursively(module, self.visitor.filepath.name)
