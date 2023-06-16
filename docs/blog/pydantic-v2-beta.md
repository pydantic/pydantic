# Pydantic V2 Beta Release

<aside class="blog" markdown>
![Terrence Dorsey](../img/terrencedorsey.jpg)
<div markdown>
  **Terrence Dorsey & Samuel Colvin** &bull;&nbsp;
  [:material-github:](https://github.com/pydantic) &bull;&nbsp;
  [:material-twitter:](https://twitter.com/pydantic) &bull;&nbsp;
  :octicons-calendar-24: June 3, 2023 &bull;&nbsp;
  :octicons-clock-24: 8 min read
</div>
</aside>

---

The beta releases of Pydantic V2 represent our final steps toward a stable release!

Working from the first Pydantic V2 alpha, we've spent the last two months making further improvements based us your feedback.

At this point, we believe that the API is stable enough for you to start using it in your production projects. We'll continue to make improvements and bug fixes, but the API is (mostly) complete.

## Getting started with the Pydantic V2 beta

We believe Pydantic V2 is ready for your production applications. This page provides a guide highlighting the most
important changes to help you migrate your code from Pydantic V1 to Pydantic V2.

To get started with the Pydantic V2 beta, install it from PyPI.

```bash
pip install --pre -U "pydantic>=2.0b3"
```

If you encounter any issues, please [create an issue in GitHub](https://github.com/pydantic/pydantic/issues)
using the `bug V2` label. This will help us to actively monitor and track errors, and to continue to improve
the library’s performance.

Thank you for your support, and we look forward to your feedback.

---

## Migration notes

We've provided an [extensive Migration Guide](../migration-guide.md) to help you migrate your code from Pydantic V1 to Pydantic V2.

In the Migration Guide you will find notes about critical changes including moved, deprecated, and removed features.

## Headlines

Here's a quick summary of the most important changes in Pydantic V2.

* Significant improvements to `BaseModel` methods and attributes.
* A new `RootModel` class.
* Significant improvements to `Field` methods and attributes.
* Changes to dataclasses
* Moving model config from `Config` to `model_config`, with accompanying changes to config settings.
* `@validator` and `@root_validator` are deprecated in favor of `@field_validator` and `@model_validator`, along with additional validation improvements.
* Introduction of `TypeAdaptor` for validating or serializing non-`BaseModel` types.
* Changes to JSON schema generation.

And much more. See the [Migration Guide](../migration-guide.md) for more details.
