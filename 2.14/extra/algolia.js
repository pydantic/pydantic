const ALGOLIA_APP_ID = 'KPPUDTIAVX';
const ALGOLIA_API_KEY = '1fc841595212a2c3afe8c24dd4cb8790';
const ALGOLIA_INDEX_NAME = 'pydantic-docs';

const { liteClient: algoliasearch } = window['algoliasearch/lite'];
const searchClient = algoliasearch(ALGOLIA_APP_ID, ALGOLIA_API_KEY);

const search = instantsearch({
  indexName: ALGOLIA_INDEX_NAME,
  searchClient,
  searchFunction(helper) {
    const query = helper.state.query

    if (query && query.length > 1) {
      document.querySelector('#hits').hidden = false
      document.querySelector('#type-to-start-searching').hidden = true
      helper.search();
    } else {
      document.querySelector('#hits').hidden = true
      document.querySelector('#type-to-start-searching').hidden = false
    }
  },
});

// create custom widget, to integrate with MkDocs built-in markup
const customSearchBox = instantsearch.connectors.connectSearchBox((renderOptions, isFirstRender) => {
  const { query, refine, clear } = renderOptions;

  if (isFirstRender) {
    document.querySelector('#searchbox').addEventListener('input', event => {
      refine(event.target.value);
    });

    document.querySelector('#searchbox').addEventListener('focus', () => {
      document.querySelector('#__search').checked = true;
    });

    document.querySelector('#searchbox-clear').addEventListener('click', () => {
      clear();
    });

    document.querySelector('#searchbox').addEventListener('keydown', (event) => {
      // on down arrow, find the first search result and focus it
      if (event.key === 'ArrowDown') {
        document.querySelector('.md-search-result__link').focus();
        event.preventDefault();
      }
    });

    // for Hits, add keyboard navigation
    document.querySelector('#hits').addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown') {
        const next = event.target.parentElement.nextElementSibling;
        if (next) {
          next.querySelector('.md-search-result__link').focus();
          event.preventDefault();
        }
      } else if (event.key === 'ArrowUp') {
        const prev = event.target.parentElement.previousElementSibling;
        if (prev) {
          prev.querySelector('.md-search-result__link').focus();
        } else {
          document.querySelector('#searchbox').focus();
        }
        event.preventDefault();
      }
    })

    document.addEventListener('keydown', (event) => {
      // if forward slash is pressed, focus the search box
      if (event.key === '/' && event.target.tagName !== 'INPUT') {
        document.querySelector('#searchbox').focus();
        event.preventDefault();
      }
    })
  }


  document.querySelector('#type-to-start-searching').hidden = query.length > 1;
  document.querySelector('#searchbox').value = query;
});

search.addWidgets([
  customSearchBox({}),

  instantsearch.widgets.hits({
    container: '#hits',
    cssClasses: {
      'list': 'md-search-result__list',
      'item': 'md-search-result__item'
    },
    templates: {
      item: (hit, { html, components }) => {
        return html`
          <a href="${hit.abs_url}" class="md-search-result__link" tabindex="-1">
            <div class="md-search-result__article md-typeset">
              <div class="md-search-result__icon md-icon"></div>
              <h1>${components.Highlight({ attribute: 'title', hit })}</h1>
              <article>${components.Snippet({ attribute: 'content', hit })} </article>
            </div>
          </a>`
      },
    },
  })
]);

search.start();
