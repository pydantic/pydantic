The Pydantic documentation is available in the [llms.txt](https://llmstxt.org/) format.
This format is defined in Markdown and suited for large language models.

Two formats are available:

* [llms.txt](https://docs.pydantic.dev/latest/llms.txt): a file containing a brief description
  of the project, along with links to the different sections of the documentation. The structure
  of this file is described in details in the [format documentation](https://llmstxt.org/#format).
* [llms-full.txt](https://docs.pydantic.dev/latest/llms-full.txt): Similar to the `llms.txt` file,
  but every link content is included. Note that this file may be too large for some LLMs.

As of today, these files *cannot* be natively leveraged by LLM frameworks or IDEs. Alternatively,
a [MCP server](https://modelcontextprotocol.io/) can be implemented to properly parse the `llms.txt`
file.
