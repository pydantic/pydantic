# Troubleshooting Validation Errors with Logfire

When a [`ValidationError`][pydantic_core.ValidationError] is raised, the message tells you *what* went
wrong: which field, which rule, and the value that triggered it. In production, the hard part is
usually everything the message *can't* show you: where that data came from, how
often it happens, and what else your application was doing at the time. By the time you read the log,
the payload that failed is often already gone.

## Getting started

Troubleshooting validation errors in production is much easier when something records them as they
happen, capturing the input alongside the error. Logfire's Pydantic integration does this: it records
each validation as it runs, so you can open the one that failed instead of reconstructing it from logs
after the fact.

If you haven't set it up yet, follow the three-step
[getting started guide](https://pydantic.dev/docs/logfire/get-started/), then instrument your application:

```python {test="skip"}
from datetime import date

import logfire

from pydantic import BaseModel

logfire.configure()
logfire.instrument_pydantic(record='failure')  # (1)!


class User(BaseModel):
    name: str
    country_code: str
    dob: date


User(name='Anne', country_code='USA', dob='not-a-date')  # (2)!
```

1. `record='failure'` records a trace for each *failed* validation, while still collecting metrics for all
   of them. Drop it (the default is `record='all'`) if you also want a trace for every successful validation.
2. This validation fails because `dob` is not a valid date. Logfire records the input, the error, and
   the surrounding context, so you can troubleshoot it without adding any logging of your own.

Once instrumented, each failed validation shows up in the live view, recorded with:

* **Its input**: the exact data passed to validation, so you don't have to reconstruct the payload from
  logs or guess what your model received.
* **Its context**: a span alongside the surrounding request, task, or trace, so you can follow bad data
  back to its source.
* **A queryable history**: every failure is stored, so you can ask "which field fails most often?"
  or "did this error spike after the last deploy?" in SQL.
* **No extra logging code**: one `logfire.instrument_pydantic()` call covers all your models; you don't
  wrap each validation attempt in a `try`/`except`.

Recording the input naturally raises the question of sensitive data, since the failing payload may
contain it. The Logfire SDK
[scrubs common sensitive values](https://pydantic.dev/docs/logfire/instrument/scrubbing/) (things
that look like passwords, tokens, or other secrets) from spans before they leave your machine, and you
can extend the rules for your own fields.

![A failed Pydantic validation recorded in the Logfire live view](../img/logfire-validation-live-view.png)

## Reading the error from the trace

Beyond the plain-language explanation, each failed validation span shows the raw structured
[`errors()`][pydantic_core.ValidationError.errors] list next to the input that produced it: the field
path (`loc`), the machine-readable `type`, and the offending value, so you can see which field failed
and with what value without parsing the rendered message string by hand.

![A Pydantic validation failure in the Logfire live view, with the structured errors captured on the span](../img/logfire-validation-error-trace.png)

## From one failure to the pattern

A single trace tells you about one failure. Often the more useful question is whether it's a one-off or
something recurring. Logfire
[groups repeated exceptions into issues](https://pydantic.dev/docs/logfire/observe/issues/), so a
validation that fails a thousand times shows up as one entry with a count and a first-seen time, rather
than a thousand lines to scroll through, which makes it easy to tell a genuine spike from background
noise.

Once you know which failures matter, you don't have to keep watching for them. Logfire
[alerts](https://pydantic.dev/docs/logfire/observe/alerts/) run a SQL query on a schedule and
notify you (for example, in Slack) when it matches. A rule like "validation failures for this model
crossed a threshold" means the next occurrence finds you instead of a user reporting it.

## Have Logfire explain the error

Open a failed validation span in [Pydantic Logfire](../integrations/logfire.md) and it explains the
failure in plain language (currently in beta), reading the structured errors and, for each field,
telling you what was expected and what it received, including the messages from your own
[custom validators](../concepts/validators.md#raising-validation-errors). You get to the fix without
memorising every [error code](validation_errors.md).

<figure markdown="span">
  ![Logfire explaining a Pydantic validation error](../img/logfire-validation-error-explained.png){ width="500" }
</figure>

If you debug with an AI coding agent, the [Logfire MCP server](https://pydantic.dev/docs/logfire/guides/mcp-server/)
lets the agent query your telemetry directly, including the input and errors from a failed validation, so it can investigate against your
real data instead of guessing.

## Learn more

* [Pydantic Logfire integration](../integrations/logfire.md): how to install and configure Logfire
  with Pydantic.
* [Logfire documentation](https://pydantic.dev/docs/logfire/get-started/): the full Logfire docs.

For a reference of the individual error types you may encounter, see
[Validation Errors](validation_errors.md) and [Usage Errors](usage_errors.md).
