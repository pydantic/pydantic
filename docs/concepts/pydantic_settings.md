---
description: Support for loading a settings or config class from environment variables or secrets files.
---

# Settings Management

[Pydantic Settings](https://github.com/pydantic/pydantic-settings) provides optional Pydantic features for loading a settings or config class from environment variables or secrets files.

Settings are validated from environment variables and secrets files, so a
[`ValidationError`][pydantic_core.ValidationError] here points at an environment value that didn't match
its field. [Logfire](../errors/troubleshooting.md) records each validation and its structured errors, so
you can see which setting failed and why.

{{ pydantic_settings }}
