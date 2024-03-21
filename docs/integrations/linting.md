## Flake8 plugin

If using Flake8 in your project, a [plugin](https://pypi.org/project/flake8-pydantic/) is available
and can be installed using the following:

```bash
pip install flake8-pydantic
```

The lint errors provided by this plugin are namespaced under the `PYDXXX` code. To ignore some unwanted
rules, the Flake8 configuration can be adapted:

```ini
[flake8]
extend-ignore = PYD001,PYD002
```
