The [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator/) project is a library and command-line utility to generate pydantic models from just about any data source, including:

* OpenAPI 3 (YAML/JSON)
* JSON Schema
* JSON/YAML Data (which will converted to JSON Schema)

Whenever you find yourself with any data convertible JSON but without pydantic models, this tool will allow you to generate type-safe model hierarchies on demand.

## Installation
```bash
pip install datamodel-code-generator
```

## Example
In this case, datamodel-code-generator creates pydantic models from a JSON Schema file.
```bash
datamodel-codegen  --input person.json --input-file-type jsonschema --output model.py
```

person.json:
```json
{
  "$id": "person.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Person",
  "type": "object",
  "properties": {
    "first_name": {
      "type": "string",
      "description": "The person's first name."
    },
    "last_name": {
      "type": "string",
      "description": "The person's last name."
    },
    "age": {
      "description": "Age in years.",
      "type": "integer",
      "minimum": 0
    },
    "pets": {
      "type": "array",
      "items": [
        {
          "$ref": "#/definitions/Pet"
        }
      ]
    },
    "comment": {
      "type": "null"
    }
  },
  "required": [
      "first_name",
      "last_name"
  ],
  "definitions": {
    "Pet": {
      "properties": {
        "name": {
          "type": "string"
        },
        "age": {
          "type": "integer"
        }
      }
    }
  }
}
```

model.py:
```py
{!.tmp_examples/generate_models_person_model.py!}
```

More information can be found on the
[official documentation](https://koxudaxi.github.io/datamodel-code-generator/)
