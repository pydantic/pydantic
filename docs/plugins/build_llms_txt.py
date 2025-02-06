from __future__ import annotations as _annotations

import os

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


def on_config(config: MkDocsConfig):
    os.makedirs(config.site_dir, exist_ok=True)
    llms_path = os.path.join(config.site_dir, 'llms.txt')
    with open(llms_path, 'w') as f:
        f.write('')


def on_page_content(html: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    # Clean up presentational and UI elements
    for element in soup.find_all(
        ['a', 'div', 'img'], attrs={'class': ['headerlink', 'tabbed-labels', 'twemoji lg middle', 'twemoji']}
    ):
        element.decompose()

    # The API reference generates HTML tables with line numbers, this strips the line numbers cell and goes back to a code block
    for extra in soup.find_all('table', attrs={'class': 'highlighttable'}):
        extra.replace_with(BeautifulSoup(f'<pre>{extra.find("code").get_text()}</pre>', 'html.parser'))

    with open(os.path.join(config.site_dir, 'llms.txt'), 'a', encoding='utf-8') as f:
        f.write(MarkdownConverter().convert_soup(soup))  # type: ignore[reportUnknownMemberType]

    return html
