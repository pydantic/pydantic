[Pydantic AI](https://pydantic.dev/docs/ai/overview/) is a Python agent framework built by the Pydantic team that uses Pydantic validation for [structured output](https://pydantic.dev/docs/ai/core-concepts/output/#structured-output) schema generation and validation.
By specifying an `output_type` on an Agent, you can constrain the LLM to return data that matches your Pydantic model schema.

## LLM Structured Output

```python {test="skip"}
from pydantic_ai import Agent

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class City(BaseModel):
    name: str
    country: str
    population: int = Field(description='Estimated population', gt=0)

    @field_validator('country')
    @classmethod
    def country_must_be_valid(cls, v: str, info: ValidationInfo) -> str:
        valid_countries: list[str] = info.context or []
        if v not in valid_countries:
            raise ValueError(f'Unknown country: {v!r}')
        return v


agent = Agent(
    'openai:gpt-5-mini',
    output_type=list[City],
    # Pydantic validation context (not sent to the model)
    validation_context=['Japan', 'United States', 'Germany'],
)

result = agent.run_sync('List the 3 largest cities in Japan')
print(result.output)
#> [City(name='Tokyo', country='Japan', population=13960000), ...]
```

!!! tip "Logfire integration"
    Pydantic AI has a complete integration with [Logfire](../integrations/logfire.md), which records
    agent runs and the validation inside them: each agent run shows the output the model produced,
    the errors your validators raised, and the retry that followed.
