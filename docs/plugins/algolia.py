# pyright: reportUnknownMemberType=false
from __future__ import annotations as _annotations

import os
from typing import TypedDict, cast

from algoliasearch.search.client import SearchClientSync
from bs4 import BeautifulSoup
from mkdocs.config import Config
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


class AlgoliaRecord(TypedDict):
    content: str
    pageID: str
    abs_url: str
    title: str
    objectID: str
    importance: int


records: list[AlgoliaRecord] = []
# these values should match docs/javascripts/search-worker.js.
ALGOLIA_APP_ID = 'KPPUDTIAVX'
ALGOLIA_INDEX_NAME = 'pydantic-docs'
ALGOLIA_WRITE_API_KEY = os.environ.get('ALGOLIA_WRITE_API_KEY')

# Algolia has a limit of 100kb per record in the paid plan,
# leave some space for the other fields as well.
MAX_CONTENT_LENGTH = 95_000


# Temporal words
temporal_words = [
    'before',
    'after',
    'during',
    'between',
    'since',
    'until',
    'from',
    'to',
    'yesterday',
    'today',
    'tomorrow',
    'past',
    'future',
    'upcoming',
    'recent',
    'previous',
    'next',
    'early',
    'late',
    'now',
    'current',
    'former',
    'latest',
]

# Articles and basic prepositions
basic_words = ['the', 'a', 'an', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'of', 'from']

# Common qualifiers
qualifiers = [
    'very',
    'quite',
    'rather',
    'somewhat',
    'mostly',
    'almost',
    'nearly',
    'approximately',
    'about',
    'around',
    'roughly',
    'mainly',
    'primarily',
    'generally',
    'typically',
    'usually',
    'normally',
]

# Action-related words
action_words = [
    'can',
    'will',
    'should',
    'must',
    'may',
    'might',
    'could',
    'would',
    'do',
    'does',
    'did',
    'done',
    'having',
    'has',
    'had',
]

# Connecting words
connecting_words = [
    'and',
    'or',
    'but',
    'yet',
    'so',
    'because',
    'therefore',
    'however',
    'although',
    'despite',
    'unless',
    'whereas',
]

# Combine all categories
optional_words = temporal_words + basic_words + qualifiers + action_words + connecting_words


# Note: alternatively, we could use a tree processor as a markdown plugin
# (see https://python-markdown.github.io/extensions/api/#treeprocessors).
def on_page_content(html: str, page: Page, config: Config, files: Files) -> str:
    if not ALGOLIA_WRITE_API_KEY:
        return html

    assert page.title is not None, 'Page title must not be None'
    title = cast(str, page.title)

    soup = BeautifulSoup(html, 'html.parser')

    for el_with_class in soup.find_all(class_=['doc-section-item', 'doc-section-title', 'doc-md-description', 'doc']):
        # delete the class attribute
        del el_with_class['class']

    # Remove title attributes from all elements
    for element in soup.find_all(attrs={'title': True}):
        del element['title']

    # Remove ids
    for element in soup.find_all(attrs={'id': True}):
        del element['id']

    # Clean up presentational and UI elements
    for element in soup.find_all(['autoref']):
        element.unwrap()

    # this removes the large source code embeds from Github
    for element in soup.find_all('details'):
        element.decompose()

    # Cleanup code examples
    for extra in soup.find_all('div', attrs={'class': 'language-python highlight'}):
        extra.replace_with(BeautifulSoup(f'<pre>{extra.find("code").get_text()}</pre>', 'html.parser'))

    # Cleanup code examples, part 2
    for extra in soup.find_all('div', attrs={'class': 'language-python doc-signature highlight'}):
        extra.replace_with(BeautifulSoup(f'<pre>{extra.find("code").get_text()}</pre>', 'html.parser'))

    # The API reference generates HTML tables with line numbers, this strips the line numbers cell and goes back to a code block
    for extra in soup.find_all('table', attrs={'class': 'highlighttable'}):
        extra.replace_with(BeautifulSoup(f'<pre>{extra.find("code").get_text()}</pre>', 'html.parser'))

    # Find all h1 and h2 headings
    headings = soup.find_all(['h1', 'h2'])

    # Process each section
    for current_heading in headings:
        heading_id = current_heading.get('id', '')
        section_title = current_heading.get_text().replace('¶', '').strip()

        # Get content until next heading
        content: list[str] = []
        sibling = current_heading.find_next_sibling()
        while sibling and sibling.name not in {'h1', 'h2'}:
            content.append(str(sibling))
            sibling = sibling.find_next_sibling()

        section_html = ''.join(content)

        # Create anchor URL
        anchor_url: str = f'{page.abs_url}#{heading_id}' if heading_id else page.abs_url or ''

        # boost the importance of pages that have concepts in their url
        pageIsFromConcepts = anchor_url.find('concepts') != -1
        importance = 10 if pageIsFromConcepts else 0

        if len(section_html) > MAX_CONTENT_LENGTH:
            print(
                f"Record with title '{title}', '{anchor_url}' has more than {MAX_CONTENT_LENGTH} characters, {len(section_html)}."
            )
            print(content)
        else:
            # print(f'Adding record for {title} - {section_title} ({len(section_html)} characters).')
            # Create record for this section
            records.append(
                AlgoliaRecord(
                    content=section_html,
                    pageID=title,
                    abs_url=anchor_url,
                    title=f'{title} - {section_title}',
                    objectID=anchor_url,
                    importance=importance,
                )
            )

    return html


def on_post_build(config: Config) -> None:
    if not ALGOLIA_WRITE_API_KEY:
        return

    client = SearchClientSync(ALGOLIA_APP_ID, ALGOLIA_WRITE_API_KEY)

    client.set_settings(
        index_name=ALGOLIA_INDEX_NAME,
        index_settings={
            'optionalWords': optional_words,
            'highlightPreTag': '<em class="search-highlight">',
            'highlightPostTag': '</em>',
            'attributesToSnippet': ['content:80'],
        },
    )

    client.clear_objects(index_name=ALGOLIA_INDEX_NAME)

    client.batch(
        index_name=ALGOLIA_INDEX_NAME,
        batch_write_params={'requests': [{'action': 'addObject', 'body': record} for record in records]},
    )
