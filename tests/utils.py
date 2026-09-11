import dataclasses

import pydantic


def dataclass_decorators(include_identity: bool = False, include_combined: bool = True):
    """A helper to parameterize a test with the Pydantic and stdlib dataclass decorator."""

    decorators = [pydantic.dataclasses.dataclass, dataclasses.dataclass]
    ids = ['pydantic', 'stdlib']

    if include_combined:

        def combined_decorator(cls):
            """
            Should be equivalent to:
            @pydantic.dataclasses.dataclass
            @dataclasses.dataclass
            """
            return pydantic.dataclasses.dataclass(dataclasses.dataclass(cls))

        decorators.append(combined_decorator)
        ids.append('combined')

    if include_identity:

        def identity_decorator(cls):
            return cls

        decorators.append(identity_decorator)
        ids.append('identity')

    return {'argvalues': decorators, 'ids': ids}
