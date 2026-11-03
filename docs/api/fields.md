::: pydantic.fields
    options:
      group_by_category: false
      members:
        - Field
        - FieldInfo
        - PrivateAttr
        - ModelPrivateAttr
        - computed_field
        - ComputedFieldInfo
      filters:
        - "!^from_field$"
        - "!^from_annotation$"
        - "!^from_annotated_attribute$"
        - "!^rebuild_annotation$"
        - "!^apply_typevars_map$"
