from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


def on_config(config: MkDocsConfig) -> None:
    config_dir = Path(config.site_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    llms_path = config_dir / 'llms.txt'
    llms_path.touch()


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

    llms_path = Path(config.site_dir) / 'llms.txt'
    with llms_path.open(mode='a', encoding='utf-8') as f:
        f.write(MarkdownConverter().convert_soup(soup))

    return html
