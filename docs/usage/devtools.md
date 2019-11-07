!!! note
    **Admission:** I (the primary developer of *pydantic*) also develop python-devtools.
    
[python-devtools](https://python-devtools.helpmanual.io/) (`pip install devtools`) provides a number of tools which
are useful during python development, including `debug()` an alternative to `print()` which formats output in a way
which should be easier to read than `print` as well as giving information about which file/line the print statement 
is on and what value was printed.

*pydantic* integrates with *devtools* by implementing the `__pretty__` method on most public classes.

In particular `debug()` is useful when inspecting models:


```py
{!.tmp_examples/devtools_main.py!}
```

Will output in your terminal:

{!.tmp_examples/devtools_main.html!}
