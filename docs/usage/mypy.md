Pydantic works with [mypy](http://mypy-lang.org/) provided you use the "annotation only" version of
required variables:

```py
{!./examples/mypy.py!}
```
_(This script is complete, it should run "as is")_

You can also run it through mypy with:

    mypy --ignore-missing-imports --follow-imports=skip --strict-optional pydantic_mypy_test.py

## Strict Optional

For your code to pass with `--strict-optional` you need to to use `Optional[]` or an alias of `Optional[]`
for all fields with `None` default, this is standard with mypy.

Pydantic provides a few useful optional or union types:

* `NoneStr` aka. `Optional[str]`
* `NoneBytes` aka. `Optional[bytes]`
* `StrBytes` aka. `Union[str, bytes]`
* `NoneStrBytes` aka. `Optional[StrBytes]`

If these aren't sufficient you can of course define your own.

## Required Fields and mypy

The ellipsis notation `...` will not work with mypy, you need to use annotation only fields as in the example above.

To get round this you can use the `Required` (via `from pydantic import Required`) field as an alias for
ellipses or annotation only.
