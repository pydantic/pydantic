*Pydantic* will raise `ValidationError` whenever it finds an error in the data it's validating.

!!! note
    Validation code should not raise `ValidationError` itself, but rather raise `ValueError` or `TypeError`
    (or subclasses thereof) which will be caught and used to populate `ValidationError`.

One exception will be raised regardless of the number of errors found, that `ValidationError` will
contain information about all the errors and how they happened.

You can access these errors in a several ways:

* **`e.errors()`** method will return list of errors found in the input data.
* **`e.json()`** method will return a JSON representation of `errors`.
* **`str(e)`** method will return a human readable representation of the errors.

Each error object contains:

* **`loc`** the error's location as a list, the first item in the list will be the field where the error occurred,
 subsequent items will represent the field where the error occurred
 in [sub models](models.md#recursive_models) when they're used.
* **`type`** a unique identifier of the error readable by a computer.
* **`msg`** a human readable explanation of the error.
* **`ctx`** an optional object which contains values required to render the error message.

To demonstrate that:

```py
{!./examples/errors1.py!}
```

(This script is complete, it should run "as is". `json()` has `indent=2` set by default, but I've tweaked the
JSON here and below to make it slightly more concise.)

In your custom data types or validators you should use `TypeError` and `ValueError` to raise errors:

```py
{!./examples/errors2.py!}
```

(This script is complete, it should run "as is")

You can also define your own error class with abilities to specify custom error code, message template and context:

```py
{!./examples/errors3.py!}
```

(This script is complete, it should run "as is")
