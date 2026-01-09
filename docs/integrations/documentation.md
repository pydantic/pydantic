---
title: "Pydantic Validation: Sphinx & MkDocs Integration"
description: "Stop manually updating API docs. Pydantic’s integrations with Sphinx and MkDocs turn your models into rich, up-to-date documentation automatically."
---
Pydantic uses [MkDocs](https://www.mkdocs.org/) for documentation, together with
[mkdocstrings](https://mkdocstrings.github.io/). As such, you can make use of Pydantic's
Sphinx object inventory to cross-reference the Pydantic API documentation.

=== "Sphinx"

    In your [Sphinx configuration](https://www.sphinx-doc.org/en/master/usage/configuration.html),
    add the following to the [`intersphinx` extension configuration](https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration):

    ```python {test="skip"}
    intersphinx_mapping = {
        'pydantic': ('https://docs.pydantic.dev/latest', None),  # (1)!
    }
    ```

    1. You can also use `dev` instead of `latest` to target the latest documentation build, up to date
       with the [`main`](https://github.com/pydantic/pydantic/tree/main) branch.

=== "mkdocstrings"

    In your [MkDocs configuration](https://www.mkdocs.org/user-guide/configuration/), add the following
    import to your [mkdocstrings plugin configuration](https://mkdocstrings.github.io/usage/#cross-references-to-other-projects-inventories):

    ```yaml
    plugins:
    - mkdocstrings:
        handlers:
          python:
            import:
            - https://docs.pydantic.dev/latest/objects.inv  # (1)!
    ```

    1. You can also use `dev` instead of `latest` to target the latest documentation build, up to date
       with the [`main`](https://github.com/pydantic/pydantic/tree/main) branch.
