from dataclasses import dataclass


@dataclass
class Schema:
    """
    Used to provide extra information about a field in a model schema. The parameters will be
    converted to validations and will add annotations to the generated JSON Schema. Some arguments
    apply only to number fields (``int``, ``float``, ``Decimal``) and some apply only to ``str``

    :param default: since the Schema is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param gt: only applies to numbers, requires the field to be "greater than". The schema
      will have an ``exclusiveMinimum`` validation keyword
    :param ge: only applies to numbers, requires the field to be "greater than or equal to". The
      schema will have a ``minimum`` validation keyword
    :param lt: only applies to numbers, requires the field to be "less than". The schema
      will have an ``exclusiveMaximum`` validation keyword
    :param le: only applies to numbers, requires the field to be "less than or equal to". The
      schema will have a ``maximum`` validation keyword
    :param min_length: only applies to strings, requires the field to have a minimum length. The
      schema will have a ``maximum`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum length. The
      schema will have a ``maxLength`` validation keyword
    :param regex: only applies to strings, requires the field match agains a regular expression
      pattern string. The schema will have a ``pattern`` validation keyword
    :param **extra: any additional keyword arguments will be added as is to the schema
    """

    __slots__ = (
        'default',
        'alias',
        'title',
        'description',
        'gt',
        'ge',
        'lt',
        'le',
        'min_length',
        'max_length',
        'regex',
        'extra',
    )

    def __init__(
        self,
        default,
        *,
        alias: str = None,
        title: str = None,
        description: str = None,
        gt: float = None,
        ge: float = None,
        lt: float = None,
        le: float = None,
        min_length: int = None,
        max_length: int = None,
        regex: str = None,
        **extra,
    ):
        self.default = default
        self.alias = alias
        self.title = title
        self.description = description
        self.extra = extra
        self.gt = gt
        self.ge = ge
        self.lt = lt
        self.le = le
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
