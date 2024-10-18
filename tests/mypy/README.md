# Mypy plugin type checking suite

> [!WARNING]
> The test suite is subject to changes. It is currently not user friendly as the output and configuration
> files are separated from the source modules, making it hard to navigate. In the future, we may switch
> to using the [`pytest-mypy-plugins`][https://github.com/TypedDjango/pytest-mypy-plugins] library, which
> provides more flexibility when it comes to merging different mypy configurations.


The `test_mypy_results` test defined in [`test_mypy.py`](./test_mypy.py) runs Mypy on the files
defined in [`modules/`](./modules/), using the configuration files from [`configs/`](./configs/).

The Mypy output is merged with the source file and saved in the [`outputs/`](./outputs/) folder.

For instance, with the following file:

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int


model = Model(a=1, b=2)
```

The output will look like:

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int


model = Model(a=1, b=2)
# MYPY: error: Unexpected keyword argument "b" for "Model"  [call-arg]
```

## Adding a new test

1. Define a new file in the [`modules/`](./modules/) folder:

   ```python
   # modules/new_test.py

   class Model(BaseModel):
       a: int


   model = Model(a=1, b=2)
   ```

2. Add the new file in the defined `cases` in [`test_mypy.py`](./test_mypy.py), together
   with a configuration file:

   ```python
   cases: list[ParameterSet | tuple[str, str]] = [
       ...,
       # One-off cases
       *[
            ('mypy-plugin.ini', 'custom_constructor.py'),
            ('mypy-plugin.ini', 'config_conditional_extra.py'),
            ...,
            ('mypy-plugin.ini', 'new_test.py'),  # <-- new test added.
        ]
   ```

3. Run `make test-mypy-update-all`. It should create a new output with your new file.

4. Make sure the output contains the expected Mypy error message/code.

> [!NOTE]
> You can also edit existing module files. In that case, only step 3 and 4 are relevant.
