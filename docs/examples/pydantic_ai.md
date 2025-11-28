[Pydantic AI](https://ai.pydantic.dev/output/#structured-output) is a Python agent framework that uses Pydantic for structured output validation.
By specifying an `output_type` on an Agent, you can constrain the LLM to return data that matches your Pydantic model schema.

## LLM Structured Output

=== "Simple"
    ```python {test="skip"}
    from pydantic import BaseModel
    from pydantic_ai import Agent

    class Person(BaseModel):
        name: str
        age: int
        occupation: str


    agent = Agent('openai:gpt-5-mini', output_type=Person)
    result = agent.run_sync('Extract: John is a 30 year old software engineer')
    print(result.output)
    #> name='John' age=30 occupation='software engineer'
    ```

=== "Advanced"
    ```python {test="skip"}
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent

    class City(BaseModel):
        name: str
        country: str
        population: int = Field(description='Estimated population')


    agent = Agent('openai:gpt-5-mini', output_type=list[City])
    result = agent.run_sync('List the 3 largest cities in Japan')
    print(result.output)
    #> [City(name='Tokyo', country='Japan', population=13960000), ...]
    ```
