!!! note
    Both postponed annotations via the future import and `ForwardRef` require python 3.7+.

Postponed annotations (as described in [PEP563](https://www.python.org/dev/peps/pep-0563/))
"just work".

```py
{!./examples/postponed_annotations.py!}
```
_(This script is complete, it should run "as is")_

Internally *pydantic*  will call a method similar to `typing.get_type_hints` to resolve annotations.

In cases where the referenced type is not yet defined, `ForwardRef` can be used (although referencing the
type directly or by its string is a simpler solution in the case of
[self-referencing models](#self-referencing-models)).

You may need to call `Model.update_forward_refs()` after creating the model,
this is because in the example below `Foo` doesn't exist before it has been created (obviously) so `ForwardRef`
can't initially be resolved. You have to wait until after `Foo` is created, then call `update_forward_refs`
to properly set types before the model can be used.

```py
{!./examples/forward_ref.py!}
```
_(This script is complete, it should run "as is")_

!!! warning
    To resolve strings (type names) into annotations (types) *pydantic* needs a dict to lookup,
    for this it uses `module.__dict__` just as `get_type_hints` does. That means *pydantic* does not play well
    with types not defined in the global scope of a module.

For example, this works fine:

```py
{!./examples/postponed_works.py!}
```

While this will break:

```py
{!./examples/postponed_broken.py!}
```

Resolving this is beyond the call for *pydantic*: either remove the future import or declare the types globally.

## Self-referencing Models

Data structures with self-referencing models are also supported, provided the function
`update_forward_refs()` is called once the model is created (you will be reminded
with a friendly error message if you don't).

Within the model, you can refer to the not-yet-constructed model by a string :

```py
{!./examples/self_referencing_string.py!}
```
_(This script is complete, it should run "as is")_

Since `python 3.7`, You can also refer it by its type, provided you import `annotations` (see
[above](postponed_annotations.md) for support depending on Python
and pydantic versions).

```py
{!./examples/self_referencing_annotations.py!}
```
_(This script is complete, it should run "as is")_
