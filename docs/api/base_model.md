Pydantic models are simply classes which inherit from `BaseModel` and define fields as annotated attributes.

::: pydantic.BaseModel
    options:
        show_root_heading: true
        merge_init_into_class: false
        group_by_category: false
        # explicit members list so we can set order and include `__init__` easily
        members:
          - __init__
          - model_config
          - model_computed_fields
          - model_extra
          - model_fields
          - model_fields_set
          - model_construct
          - model_copy
          - model_dump
          - model_dump_json
          - model_json_schema
          - model_parametrized_name
          - model_post_init
          - model_rebuild
          - model_validate
          - model_validate_json
          - model_validate_strings
          - copy

::: pydantic.create_model
    options:
        show_root_heading: true
