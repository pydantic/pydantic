First of all, we recognize that the transitions from Pydantic V1 to V2 has been and will be painful for some users.
We're sorry about this pain :pray:, it was an unfortunate but necessary step to correct design mistakes of V1.

**There will not be another breaking change of this magnitude!**

## Pydantic V1

Active development of V1 has already stopped, however critical bug fixes and security vulnerabilities will be fixed in V1 for **one year** after the release of V2 (June 30, 2024).

## Pydantic V2

We will not intentionally make breaking changes in minor releases of V2.

Methods marked as `deprecated` will not be removed until the next major release, V3.

Of course some apparently safe changes and bug fixes will inevitably break some users' code &mdash; obligatory link to [XKCD](https://m.xkcd.com/1172/).

The following changes will **NOT** be considered breaking changes, and may occur in minor releases:

* Changing the format of `ref` as used in JSON Schema.
* Changing the `msg`, `ctx`, and `loc` fields of `ValidationError` errors. `type` will not change &mdash; if you're programmatically parsing error messages, you should use `type`.
* Adding new keys to `ValidationError` errors &mdash; e.g. we intend to add `line_number` and `column_number` to errors when validating JSON once we migrate to a new JSON parser.
* Adding new `ValidationError` errors.
* Changing `repr` even of public classes.

In all cases we will aim to minimize churn and do so only when justified by the increase of quality of `pydantic` for users.

## Pydantic V3 and beyond

We expect to make new major releases roughly once a year going forward, although as mentioned above, any associated breaking changes should be trivial to fix compared to the V1-to-V2 transition.

## Experimental Features

At Pydantic, we like to move quickly and innovate! To that end, we may introduce experimental features in minor releases.

!!! abstract "Usage Documentation"
    To learn more about our current experimental features, see the [experimental features documentation](./concepts/experimental.md).

Please keep in mind, experimental features are active works in progress. If these features are successful, they'll eventually beocme part of Pydantic. If unsuccessful, said features will be removed with little notice. While in its experimental phase, a feature's API and behaviors may not be stable, and it's very possible that changes made to the feature will not be backward-compatible.

### Naming Conventions

We use one of the following naming conventions to indicate that a feature is experimental:

1. The feature is located in the `experimental` module. In this case, you can access the feature like this:

    ```python
    from pydantic.experimental import feature_name
    ```

2. The feature is located in the main module, but prefixed with `experimental_`. This case occurs when we add a new field, argument, or method to an existing data structure already within the main `pydantic` module.

New features with these naming conventions are subject to change or removal, and we are looking for feedback and suggestions before making them a permanent part of Pydantic. See the [feedback section](./concepts/experimental.md#feedback) for more information.

### Importing Experimental Features

When you import an experimental feature from the `experimental` module, you'll see a warning message that the feature is experimental. You can disable this warning with the following:

```python
import warnings

from pydantic import PydanticExperimentalWarning

warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
```

### Lifecycle of Experimental Features

1. A new feature is added, either in the `experimental` module or with the `experimental_` prefix.
2. The behavior is often modified during patch/minor releases, with potential API/behavior changes.
3. If the feature is successful, we promote it to Pydantic with the following steps:
    a. If it was in the `experimental` module, the feature is cloned to Pydantic's main module. The original experimental feature still remains in the `experimental` module, but it will show a warning when used. If the feature was already in the main Pydantic module, we create a copy of the feature without the `experimental_` prefix, so the feature exists with both the official and experimental names. A deprecation warning is attached to the experimental version.
    b. At some point, the code of the experimental feature is removed, but there will still be a stub of the feature that provides an error message with appropriate instructions.
    c. As a last step, the experimental version of the feature is entirely removed from the codebase.

If the feature is unsuccessful or unpopular, it's removed with little notice. A stub will remain in the location of the deprecated feature with an error message.

Thanks to [streamlit](https://docs.streamlit.io/develop/quick-reference/prerelease) for the inspiration for the lifecycle and naming conventions of our new experimental feature patterns.

## Support for Python versions

Pydantic will drop support for a Python version when the following conditions are met:

* The Python version has reached [EOL](https://devguide.python.org/versions/).
* <5% of downloads of the most recent minor release need to be using that version.
