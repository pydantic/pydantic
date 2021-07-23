Testing and providing fix for bug with nested dataclass sub-types.

    If an instance of pydantic.dataclasses.dataclass has an attribute a with an annotated type A which is a built in dataclasses.dataclass
    When a value is assigned to a which is a subclass of type A - let's call this type B
    Then validation should succeed provided that the the instance of type B is itself valid.

This change ensures that the value is validated against a pydantic dataclass model which is based on the correct model targetting the appropriate subclass.