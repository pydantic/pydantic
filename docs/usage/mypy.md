*pydantic* models work with [mypy](http://mypy-lang.org/) provided you use the annotation-only version of
required fields:

```py
{!.tmp_examples/mypy_main.py!}
```

You can run your code through mypy with:

```bash
mypy \
  --ignore-missing-imports \
  --follow-imports=skip \
  --strict-optional \
  pydantic_mypy_test.py
```

If you call mypy on the example code above, you should see mypy detect the attribute access error:
```
13: error: "Model" has no attribute "middle_name"
```

## Strict Optional

For your code to pass with `--strict-optional`, you need to to use `Optional[]` or an alias of `Optional[]`
for all fields with `None` as the default. (This is standard with mypy.)

Pydantic provides a few useful optional or union types:

* `NoneStr` aka. `Optional[str]`
* `NoneBytes` aka. `Optional[bytes]`
* `StrBytes` aka. `Union[str, bytes]`
* `NoneStrBytes` aka. `Optional[StrBytes]`

If these aren't sufficient you can of course define your own.

## Mypy Plugin

Pydantic ships with a mypy plugin that adds a number of important pydantic-specific
features to mypy that improve its ability to type-check your code.

See the [pydantic mypy plugin docs](../mypy_plugin.md) for more details.


## Other pydantic interfaces

Pydantic [dataclasses](dataclasses.md) and the [`validate_arguments` decorator](validation_decorator.md)
should also work well with mypy.
