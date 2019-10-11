!!! note
    **Admission:** I (Samuel Colvin, the primary developer of *pydantic*) also develop python-devtools.
    
[python-devtools](https://python-devtools.helpmanual.io/) (`pip install devtools`) provides a number of tools which
are useful during python development, including `debug()` an alternative to `print()` which formats output in a way
which should be easier to read as well as giving information about where the print statement is and what was is printed.

*pydantic* integrates with *devtools* by implementing the `__pretty__` method on most public classes.

In particular `debug()` is useful when inspecting models:


```py
{!examples/ex_debug.py!}
```

Will output in your terminal:

<div class="terminal">
<!-- generate examples/ex_debug.html with 
      PY_DEVTOOLS_HIGHLIGHT=true python docs/examples/ex_debug.py | ansi2html -p > docs/examples/ex_debug.html
-->
<pre class="terminal-content">
{!examples/ex_debug.html!}
</pre>
</div>
