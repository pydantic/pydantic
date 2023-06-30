First of all, we recognize that the transitions from Pydantic V1 to V2 has been and will be painful for some users.
We're sorry about this pain :pray:, it was an unfortunate but necessary step to correct design mistakes of V1.

**There will not be another breaking change of this magnitude!**

## Pydantic V1 Support

Active development of V1 has already stopped, however critical bug fixes and security vulnerabilities will be fixed in V1 for **one year** after the release of V2.

## Pydantic V2 Changes

We will not intentionally make breaking changes in minor releases of V2.

Methods marked as `deprecated` will not be removed until the next major release, V3.

Of course some apparently safe changes and bug fixes will inevitably break some users' code &mdash; obligatory link to [XKCD](https://m.xkcd.com/1172/).

The following changes will **NOT** be considered breaking changes, and may occur in minor releases:

* Changing the format of `ref` as used in JSON Schema.
* Changing the `message` and `context` fields of `ValidationError` errors, `type` will not change &mdash; if you're programmatically parsing error messages, you should use `type`.
* Adding new keys to `ValidationError` errors &mdash; e.g. we intend to add `line_number` and `column_number` to errors when validating JSON once we migrate to a new JSON parser.
* Adding new `ValidationError` errors.
* Changing `repr` even of public classes.

## Pydantic V3 and beyond

We expect to make new major releases roughly once a year going forward, although as mentioned above, any associated breaking changes should be trivial to fix compared to the V1-to-V2 transition.
