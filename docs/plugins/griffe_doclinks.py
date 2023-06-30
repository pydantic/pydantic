import ast
import re
from functools import partial
from pathlib import Path

from griffe.extensions import VisitorExtension
from pymdownx.slugs import slugify

DOCS_PATH = Path(__file__).parent.parent
slugifier = slugify(case='lower')


def find_heading(content: str, slug: str, file_name: Path) -> tuple[str, int]:
    for m in re.finditer('^#+ (.+)', content, flags=re.M):
        heading = m.group(1)
        h_slug = slugifier(heading, '-')
        if h_slug == slug:
            return heading, m.end()
    raise ValueError(f'heading {slug!r} not found in {file_name}')


def replace_links(m: re.Match[str], *, file_name: str, object_name: str) -> str:
    usage_path, slug = m.groups()
    rel_file = f'{usage_path}.md'
    file_path = DOCS_PATH / rel_file
    content = file_path.read_text()
    heading, heading_end = find_heading(content, slug, file_path)
    api_link = f'pydantic.{file_name}.{object_name}'
    if f'[{api_link}]' not in content[heading_end : heading_end + 200]:
        print(f'inserting API link "{api_link}" into {file_path.relative_to(DOCS_PATH)}')
        file_path.write_text(
            f'{content[:heading_end]}'
            '??? api "API Documentation"\n\n'
            f'    [`{api_link}`][{api_link}]<br>\n\n'
            f'{content[heading_end:]}'
        )

    return f'!!! abstract "Usage Documentation"\n\n    [{heading}](../{rel_file}#{slug})\n'


class Extension(VisitorExtension):
    def visit(self, node: ast.AST) -> None:
        current_object = self.visitor.current
        if current_object and current_object.docstring:
            current_object.docstring.value = re.sub(
                r'usage[\- ]docs: ?https://docs\.pydantic\.dev/.+?/(.+?)/?#(\S+)',
                partial(replace_links, file_name=self.visitor.filepath.name[:-3], object_name=current_object.name),
                current_object.docstring.value,
            )
