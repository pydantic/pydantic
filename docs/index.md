[![CI](https://github.com/pydantic/pydantic/workflows/CI/badge.svg?event=push)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amaster+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/samuelcolvin/pydantic.svg)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amaster+workflow%3ACI)
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)
[![license](https://img.shields.io/github/license/samuelcolvin/pydantic.svg)](https://github.com/pydantic/pydantic/blob/master/LICENSE)

{!.version.md!}

Data validation and settings management using Python type annotations.

*pydantic* enforces type hints at runtime, and provides user friendly errors when data is invalid.

Define how data should be in pure, canonical Python; validate it with *pydantic*.

## Sponsors

Development of *pydantic* is made possible by the following sponsors:

<div class="sponsors">
  <div>
    <a rel="sponsored" target="_blank" href="https://www.salesforce.com">
      <img src="./sponsor_logos/salesforce.png" alt="Salesforce" />
      Salesforce
    </a>
  </div>
  <div>
    <a rel="sponsored" target="_blank" href="https://fastapi.tiangolo.com">
      <img src="./sponsor_logos/fastapi.png" alt="FastAPI" />
      FastAPI
    </a>
  </div>
  <div>
    <a rel="sponsored" target="_blank" href="https://tutorcruncher.com/?utm_source=pydantic&utm_campaign=open_source">
      <img src="./sponsor_logos/tutorcruncher.png" alt="TutorCruncher" />
      TutorCruncher
    </a>
  </div>
  <div>
    <a rel="sponsored" target="_blank" href="https://www.exoflare.com/open-source/?utm_source=pydantic&utm_campaign=open_source">
      <img src="./sponsor_logos/exoflare.png" alt="ExoFlare" />
      ExoFlare
    </a>
  </div>
  <div>
    <a rel="sponsored" target="_blank" href="https://home.robusta.dev">
      <img src="./sponsor_logos/robusta.png" alt="Robusta" />
      Robusta
    </a>
  </div>
  <div>
    <a rel="sponsored" target="_blank" href="https://www.sendcloud.com">
      <img src="./sponsor_logos/sendcloud.png" alt="SendCloud" />
      SendCloud
    </a>
  </div>
</div>

And many more who kindly sponsor Samuel Colvin on [GitHub Sponsors](https://github.com/sponsors/samuelcolvin#sponsors).

<script>
  // randomize the order of sponsors
  const ul = document.querySelector('.sponsors')
  for (let i = ul.children.length; i >= 0; i--) {
    ul.appendChild(ul.children[Math.random() * i | 0])
  }
</script>

## Example

```py
{!.tmp_examples/index_main.py!}
```
_(This script is complete, it should run "as is")_

What's going on here:

* `id` is of type int; the annotation-only declaration tells *pydantic* that this field is required. Strings,
  bytes or floats will be coerced to ints if possible; otherwise an exception will be raised.
* `name` is inferred as a string from the provided default; because it has a default, it is not required.
* `signup_ts` is a datetime field which is not required (and takes the value ``None`` if it's not supplied).
  *pydantic* will process either a unix timestamp int (e.g. `1496498400`) or a string representing the date & time.
* `friends` uses Python's typing system, and requires a list of integers. As with `id`, integer-like objects
  will be converted to integers.

If validation fails pydantic will raise an error with a breakdown of what was wrong:

```py
{!.tmp_examples/index_error.py!}
```
outputs:
```json
{!.tmp_examples/index_error.json!}
```

## Rationale

So *pydantic* uses some cool new language features, but why should I actually go and use it?

**plays nicely with your IDE/linter/brain**
: There's no new schema definition micro-language to learn. If you know how to use Python type hints, 
  you know how to use *pydantic*. Data structures are just instances of classes you define with type annotations, 
  so auto-completion, linting, [mypy](usage/mypy.md), IDEs (especially [PyCharm](pycharm_plugin.md)), 
  and your intuition should all work properly with your validated data.

**dual use**
: *pydantic's* [BaseSettings](usage/settings.md) class allows *pydantic* to be used in both a "validate this request
  data" context and in a "load my system settings" context. The main differences are that system settings can
  be read from environment variables, and more complex objects like DSNs and Python objects are often required.

**fast**
: *pydantic* has always taken performance seriously, most of the library is compiled with cython giving a ~50% speedup,
  it's generally as fast or faster than most similar libraries.

**validate complex structures**
: use of [recursive *pydantic* models](usage/models.md#recursive-models), `typing`'s 
  [standard types](usage/types.md#standard-library-types) (e.g. `List`, `Tuple`, `Dict` etc.) and 
  [validators](usage/validators.md) allow
  complex data schemas to be clearly and easily defined, validated, and parsed.

**extensible**
: *pydantic* allows [custom data types](usage/types.md#custom-data-types) to be defined or you can extend validation 
  with methods on a model decorated with the [`validator`](usage/validators.md) decorator.
  
**dataclasses integration**
: As well as `BaseModel`, *pydantic* provides
  a [`dataclass`](usage/dataclasses.md) decorator which creates (almost) vanilla Python dataclasses with input
  data parsing and validation.

## Using Pydantic

Hundreds of organisations and packages are using *pydantic*, including:

[FastAPI](https://fastapi.tiangolo.com/)
: a high performance API framework, easy to learn,
  fast to code and ready for production, based on *pydantic* and Starlette.

[Project Jupyter](https://jupyter.org/)
: developers of the Jupyter notebook are using *pydantic* 
  [for subprojects](https://github.com/pydantic/pydantic/issues/773), through the FastAPI-based Jupyter server
  [Jupyverse](https://github.com/jupyter-server/jupyverse), and for [FPS](https://github.com/jupyter-server/fps)'s
  configuration management.

**Microsoft**
: are using *pydantic* (via FastAPI) for 
  [numerous services](https://github.com/tiangolo/fastapi/pull/26#issuecomment-463768795), some of which are 
  "getting integrated into the core Windows product and some Office products."

**Amazon Web Services**
: are using *pydantic* in [gluon-ts](https://github.com/awslabs/gluon-ts), an open-source probabilistic time series
  modeling library.

**The NSA**
: are using *pydantic* in [WALKOFF](https://github.com/nsacyber/WALKOFF), an open-source automation framework.

**Uber**
: are using *pydantic* in [Ludwig](https://github.com/uber/ludwig), an open-source TensorFlow wrapper.

**Cuenca**
: are a Mexican neobank that uses *pydantic* for several internal
  tools (including API validation) and for open source projects like
  [stpmex](https://github.com/cuenca-mx/stpmex-python), which is used to process real-time, 24/7, inter-bank
  transfers in Mexico.

[The Molecular Sciences Software Institute](https://molssi.org)
: are using *pydantic* in [QCFractal](https://github.com/MolSSI/QCFractal), a massively distributed compute framework
  for quantum chemistry.

[Reach](https://www.reach.vote)
: trusts *pydantic* (via FastAPI) and [*arq*](https://github.com/samuelcolvin/arq) (Samuel's excellent
  asynchronous task queue) to reliably power multiple mission-critical microservices.

[Robusta.dev](https://robusta.dev/)
: are using *pydantic* to automate Kubernetes troubleshooting and maintenance. For example, their open source
  [tools to debug and profile Python applications on Kubernetes](https://home.robusta.dev/python/) use
  *pydantic* models.

For a more comprehensive list of open-source projects using *pydantic* see the 
[list of dependents on github](https://github.com/pydantic/pydantic/network/dependents).

## Discussion of Pydantic

Podcasts and videos discussing pydantic.

[Talk Python To Me](https://talkpython.fm/episodes/show/313/automate-your-data-exchange-with-pydantic){target=_blank}
: Michael Kennedy and Samuel Colvin, the creator of *pydantic*, dive into the history of pydantic and its many uses and benefits.

[Podcast.\_\_init\_\_](https://www.pythonpodcast.com/pydantic-data-validation-episode-263/){target=_blank}
: Discussion about where *pydantic* came from and ideas for where it might go next with 
  Samuel Colvin the creator of pydantic.

[Python Bytes Podcast](https://pythonbytes.fm/episodes/show/157/oh-hai-pandas-hold-my-hand){target=_blank}
: "*This is a sweet simple framework that solves some really nice problems... Data validations and settings management 
  using Python type annotations, and it's the Python type annotations that makes me really extra happy... It works 
  automatically with all the IDE's you already have.*" --Michael Kennedy

[Python pydantic Introduction – Give your data classes super powers](https://www.youtube.com/watch?v=WJmqgJn9TXg){target=_blank}
: a talk by Alexander Hultnér originally for the Python Pizza Conference introducing new users to pydantic and walking 
  through the core features of pydantic.
