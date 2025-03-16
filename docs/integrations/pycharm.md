While pydantic will work well with any IDE out of the box, a
[PyCharm plugin](https://plugins.jetbrains.com/plugin/12861-pydantic)
offering improved pydantic integration is available on the JetBrains Plugins Repository for PyCharm.
You can install the plugin for free from the plugin marketplace
(PyCharm's Preferences -> Plugin -> Marketplace -> search "pydantic").

The plugin currently supports the following features:

* For `pydantic.BaseModel.__init__`:
  * Inspection
  * Autocompletion
  * Type-checking

* For fields of `pydantic.BaseModel`:
  * Refactor-renaming fields updates `__init__` calls, and affects sub- and super-classes
  * Refactor-renaming `__init__` keyword arguments updates field names, and affects sub- and super-classes

More information can be found on the
[official plugin page](https://plugins.jetbrains.com/plugin/12861-pydantic)
and [Github repository](https://github.com/koxudaxi/pydantic-pycharm-plugin).
