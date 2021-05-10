from configparser import ConfigParser
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type as TypingType, Union

from mypy.errorcodes import ErrorCode
from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_OPT,
    ARG_POS,
    ARG_STAR2,
    MDEF,
    Argument,
    AssignmentStmt,
    Block,
    CallExpr,
    ClassDef,
    Context,
    Decorator,
    EllipsisExpr,
    FuncBase,
    FuncDef,
    JsonDict,
    MemberExpr,
    NameExpr,
    PassStmt,
    PlaceholderNode,
    RefExpr,
    StrExpr,
    SymbolNode,
    SymbolTableNode,
    TempNode,
    TypeInfo,
    TypeVarExpr,
    Var,
)
from mypy.options import Options
from mypy.plugin import CheckerPluginInterface, ClassDefContext, MethodContext, Plugin, SemanticAnalyzerPluginInterface
from mypy.plugins import dataclasses
from mypy.semanal import set_callable_name  # type: ignore
from mypy.server.trigger import make_wildcard_trigger
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    NoneType,
    Type,
    TypeOfAny,
    TypeType,
    TypeVarDef,
    TypeVarType,
    UnionType,
    get_proper_type,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name

CONFIGFILE_KEY = 'pydantic-mypy'
METADATA_KEY = 'pydantic-mypy-metadata'
BASEMODEL_FULLNAME = 'pydantic.main.BaseModel'
BASESETTINGS_FULLNAME = 'pydantic.env_settings.BaseSettings'
FIELD_FULLNAME = 'pydantic.fields.Field'
DATACLASS_FULLNAME = 'pydantic.dataclasses.dataclass'


def plugin(version: str) -> 'TypingType[Plugin]':
    """
    `version` is the mypy version string

    We might want to use this to print a warning if the mypy version being used is
    newer, or especially older, than we expect (or need).
    """
    return PydanticPlugin


class PydanticPlugin(Plugin):
    def __init__(self, options: Options) -> None:
        self.plugin_config = PydanticPluginConfig(options)
        super().__init__(options)

    def get_base_class_hook(self, fullname: str) -> 'Optional[Callable[[ClassDefContext], None]]':
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):  # pragma: no branch
            # No branching may occur if the mypy cache has not been cleared
            if any(get_fullname(base) == BASEMODEL_FULLNAME for base in sym.node.mro):
                return self._pydantic_model_class_maker_callback
        return None

    def get_method_hook(self, fullname: str) -> Optional[Callable[[MethodContext], Type]]:
        if fullname.endswith('.from_orm'):
            return from_orm_callback
        return None

    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname == DATACLASS_FULLNAME:
            return dataclasses.dataclass_class_maker_callback
        return None

    def _pydantic_model_class_maker_callback(self, ctx: ClassDefContext) -> None:
        transformer = PydanticModelTransformer(ctx, self.plugin_config)
        transformer.transform()


class PydanticPluginConfig:
    __slots__ = ('init_forbid_extra', 'init_typed', 'warn_required_dynamic_aliases', 'warn_untyped_fields')
    init_forbid_extra: bool
    init_typed: bool
    warn_required_dynamic_aliases: bool
    warn_untyped_fields: bool

    def __init__(self, options: Options) -> None:
        if options.config_file is None:  # pragma: no cover
            return
        plugin_config = ConfigParser()
        plugin_config.read(options.config_file)
        for key in self.__slots__:
            setting = plugin_config.getboolean(CONFIGFILE_KEY, key, fallback=False)
            setattr(self, key, setting)


def from_orm_callback(ctx: MethodContext) -> Type:
    """
    Raise an error if orm_mode is not enabled
    """
    model_type: Instance
    if isinstance(ctx.type, CallableType) and isinstance(ctx.type.ret_type, Instance):
        model_type = ctx.type.ret_type  # called on the class
    elif isinstance(ctx.type, Instance):
        model_type = ctx.type  # called on an instance (unusual, but still valid)
    else:  # pragma: no cover
        detail = f'ctx.type: {ctx.type} (of type {ctx.type.__class__.__name__})'
        error_unexpected_behavior(detail, ctx.api, ctx.context)
        return ctx.default_return_type
    pydantic_metadata = model_type.type.metadata.get(METADATA_KEY)
    if pydantic_metadata is None:
        return ctx.default_return_type
    orm_mode = pydantic_metadata.get('config', {}).get('orm_mode')
    if orm_mode is not True:
        error_from_orm(get_name(model_type.type), ctx.api, ctx.context)
    return ctx.default_return_type


class PydanticModelTransformer:
    tracked_config_fields: Set[str] = {
        'extra',
        'allow_mutation',
        'frozen',
        'orm_mode',
        'allow_population_by_field_name',
        'alias_generator',
    }

    def __init__(self, ctx: ClassDefContext, plugin_config: PydanticPluginConfig) -> None:
        self._ctx = ctx
        self.plugin_config = plugin_config

    def transform(self) -> None:
        """
        Configures the BaseModel subclass according to the plugin settings.

        In particular:
        * determines the model config and fields,
        * adds a fields-aware signature for the initializer and construct methods
        * freezes the class if allow_mutation = False or frozen = True
        * stores the fields, config, and if the class is settings in the mypy metadata for access by subclasses
        """
        ctx = self._ctx
        info = self._ctx.cls.info

        config = self.collect_config()
        fields = self.collect_fields(config)
        for field in fields:
            if info[field.name].type is None:
                if not ctx.api.final_iteration:
                    ctx.api.defer()
        is_settings = any(get_fullname(base) == BASESETTINGS_FULLNAME for base in info.mro[:-1])
        self.add_initializer(fields, config, is_settings)
        self.add_construct_method(fields)
        self.set_frozen(fields, frozen=config.allow_mutation is False or config.frozen is True)
        info.metadata[METADATA_KEY] = {
            'fields': {field.name: field.serialize() for field in fields},
            'config': config.set_values_dict(),
        }

    def collect_config(self) -> 'ModelConfigData':
        """
        Collects the values of the config attributes that are used by the plugin, accounting for parent classes.
        """
        ctx = self._ctx
        cls = ctx.cls
        config = ModelConfigData()
        for stmt in cls.defs.body:
            if not isinstance(stmt, ClassDef):
                continue
            if stmt.name == 'Config':
                for substmt in stmt.defs.body:
                    if not isinstance(substmt, AssignmentStmt):
                        continue
                    config.update(self.get_config_update(substmt))
                if (
                    config.has_alias_generator
                    and not config.allow_population_by_field_name
                    and self.plugin_config.warn_required_dynamic_aliases
                ):
                    error_required_dynamic_aliases(ctx.api, stmt)
        for info in cls.info.mro[1:]:  # 0 is the current class
            if METADATA_KEY not in info.metadata:
                continue

            # Each class depends on the set of fields in its ancestors
            ctx.api.add_plugin_dependency(make_wildcard_trigger(get_fullname(info)))
            for name, value in info.metadata[METADATA_KEY]['config'].items():
                config.setdefault(name, value)
        return config

    def collect_fields(self, model_config: 'ModelConfigData') -> List['PydanticModelField']:
        """
        Collects the fields for the model, accounting for parent classes
        """
        # First, collect fields belonging to the current class.
        ctx = self._ctx
        cls = self._ctx.cls
        fields = []  # type: List[PydanticModelField]
        known_fields = set()  # type: Set[str]
        for stmt in cls.defs.body:
            if not isinstance(stmt, AssignmentStmt):  # `and stmt.new_syntax` to require annotation
                continue

            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                continue

            if not stmt.new_syntax and self.plugin_config.warn_untyped_fields:
                error_untyped_fields(ctx.api, stmt)

            # if lhs.name == '__config__':  # BaseConfig not well handled; I'm not sure why yet
            #     continue

            sym = cls.info.names.get(lhs.name)
            if sym is None:  # pragma: no cover
                # This is likely due to a star import (see the dataclasses plugin for a more detailed explanation)
                # This is the same logic used in the dataclasses plugin
                continue

            node = sym.node
            if isinstance(node, PlaceholderNode):  # pragma: no cover
                # See the PlaceholderNode docstring for more detail about how this can occur
                # Basically, it is an edge case when dealing with complex import logic
                # This is the same logic used in the dataclasses plugin
                continue
            if not isinstance(node, Var):
                continue

            # x: ClassVar[int] is ignored by dataclasses.
            if node.is_classvar:
                continue

            is_required = self.get_is_required(cls, stmt, lhs)
            alias, has_dynamic_alias = self.get_alias_info(stmt)
            if (
                has_dynamic_alias
                and not model_config.allow_population_by_field_name
                and self.plugin_config.warn_required_dynamic_aliases
            ):
                error_required_dynamic_aliases(ctx.api, stmt)
            fields.append(
                PydanticModelField(
                    name=lhs.name,
                    is_required=is_required,
                    alias=alias,
                    has_dynamic_alias=has_dynamic_alias,
                    line=stmt.line,
                    column=stmt.column,
                )
            )
            known_fields.add(lhs.name)
        all_fields = fields.copy()
        for info in cls.info.mro[1:]:  # 0 is the current class, -2 is BaseModel, -1 is object
            if METADATA_KEY not in info.metadata:
                continue

            superclass_fields = []
            # Each class depends on the set of fields in its ancestors
            ctx.api.add_plugin_dependency(make_wildcard_trigger(get_fullname(info)))

            for name, data in info.metadata[METADATA_KEY]['fields'].items():
                if name not in known_fields:
                    field = PydanticModelField.deserialize(info, data)
                    known_fields.add(name)
                    superclass_fields.append(field)
                else:
                    (field,) = [a for a in all_fields if a.name == name]
                    all_fields.remove(field)
                    superclass_fields.append(field)
            all_fields = superclass_fields + all_fields
        return all_fields

    def add_initializer(self, fields: List['PydanticModelField'], config: 'ModelConfigData', is_settings: bool) -> None:
        """
        Adds a fields-aware `__init__` method to the class.

        The added `__init__` will be annotated with types vs. all `Any` depending on the plugin settings.
        """
        ctx = self._ctx
        typed = self.plugin_config.init_typed
        use_alias = config.allow_population_by_field_name is not True
        force_all_optional = is_settings or bool(
            config.has_alias_generator and not config.allow_population_by_field_name
        )
        init_arguments = self.get_field_arguments(
            fields, typed=typed, force_all_optional=force_all_optional, use_alias=use_alias
        )
        if not self.should_init_forbid_extra(fields, config):
            var = Var('kwargs')
            init_arguments.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))
        add_method(ctx, '__init__', init_arguments, NoneType())

    def add_construct_method(self, fields: List['PydanticModelField']) -> None:
        """
        Adds a fully typed `construct` classmethod to the class.

        Similar to the fields-aware __init__ method, but always uses the field names (not aliases),
        and does not treat settings fields as optional.
        """
        ctx = self._ctx
        set_str = ctx.api.named_type('__builtins__.set', [ctx.api.named_type('__builtins__.str')])
        optional_set_str = UnionType([set_str, NoneType()])
        fields_set_argument = Argument(Var('_fields_set', optional_set_str), optional_set_str, None, ARG_OPT)
        construct_arguments = self.get_field_arguments(fields, typed=True, force_all_optional=False, use_alias=False)
        construct_arguments = [fields_set_argument] + construct_arguments

        obj_type = ctx.api.named_type('__builtins__.object')
        self_tvar_name = '_PydanticBaseModel'  # Make sure it does not conflict with other names in the class
        tvar_fullname = ctx.cls.fullname + '.' + self_tvar_name
        tvd = TypeVarDef(self_tvar_name, tvar_fullname, -1, [], obj_type)
        self_tvar_expr = TypeVarExpr(self_tvar_name, tvar_fullname, [], obj_type)
        ctx.cls.info.names[self_tvar_name] = SymbolTableNode(MDEF, self_tvar_expr)
        self_type = TypeVarType(tvd)
        add_method(
            ctx,
            'construct',
            construct_arguments,
            return_type=self_type,
            self_type=self_type,
            tvar_def=tvd,
            is_classmethod=True,
        )

    def set_frozen(self, fields: List['PydanticModelField'], frozen: bool) -> None:
        """
        Marks all fields as properties so that attempts to set them trigger mypy errors.

        This is the same approach used by the attrs and dataclasses plugins.
        """
        info = self._ctx.cls.info
        for field in fields:
            sym_node = info.names.get(field.name)
            if sym_node is not None:
                var = sym_node.node
                assert isinstance(var, Var)
                var.is_property = frozen
            else:
                var = field.to_var(info, use_alias=False)
                var.info = info
                var.is_property = frozen
                var._fullname = get_fullname(info) + '.' + get_name(var)
                info.names[get_name(var)] = SymbolTableNode(MDEF, var)

    def get_config_update(self, substmt: AssignmentStmt) -> Optional['ModelConfigData']:
        """
        Determines the config update due to a single statement in the Config class definition.

        Warns if a tracked config attribute is set to a value the plugin doesn't know how to interpret (e.g., an int)
        """
        lhs = substmt.lvalues[0]
        if not (isinstance(lhs, NameExpr) and lhs.name in self.tracked_config_fields):
            return None
        if lhs.name == 'extra':
            if isinstance(substmt.rvalue, StrExpr):
                forbid_extra = substmt.rvalue.value == 'forbid'
            elif isinstance(substmt.rvalue, MemberExpr):
                forbid_extra = substmt.rvalue.name == 'forbid'
            else:
                error_invalid_config_value(lhs.name, self._ctx.api, substmt)
                return None
            return ModelConfigData(forbid_extra=forbid_extra)
        if lhs.name == 'alias_generator':
            has_alias_generator = True
            if isinstance(substmt.rvalue, NameExpr) and substmt.rvalue.fullname == 'builtins.None':
                has_alias_generator = False
            return ModelConfigData(has_alias_generator=has_alias_generator)
        if isinstance(substmt.rvalue, NameExpr) and substmt.rvalue.fullname in ('builtins.True', 'builtins.False'):
            return ModelConfigData(**{lhs.name: substmt.rvalue.fullname == 'builtins.True'})
        error_invalid_config_value(lhs.name, self._ctx.api, substmt)
        return None

    @staticmethod
    def get_is_required(cls: ClassDef, stmt: AssignmentStmt, lhs: NameExpr) -> bool:
        """
        Returns a boolean indicating whether the field defined in `stmt` is a required field.
        """
        expr = stmt.rvalue
        if isinstance(expr, TempNode):
            # TempNode means annotation-only, so only non-required if Optional
            value_type = get_proper_type(cls.info[lhs.name].type)
            if isinstance(value_type, UnionType) and any(isinstance(item, NoneType) for item in value_type.items):
                # Annotated as Optional, or otherwise having NoneType in the union
                return False
            return True
        if isinstance(expr, CallExpr) and isinstance(expr.callee, RefExpr) and expr.callee.fullname == FIELD_FULLNAME:
            # The "default value" is a call to `Field`; at this point, the field is
            # only required if default is Ellipsis (i.e., `field_name: Annotation = Field(...)`)
            return len(expr.args) > 0 and expr.args[0].__class__ is EllipsisExpr
        # Only required if the "default value" is Ellipsis (i.e., `field_name: Annotation = ...`)
        return isinstance(expr, EllipsisExpr)

    @staticmethod
    def get_alias_info(stmt: AssignmentStmt) -> Tuple[Optional[str], bool]:
        """
        Returns a pair (alias, has_dynamic_alias), extracted from the declaration of the field defined in `stmt`.

        `has_dynamic_alias` is True if and only if an alias is provided, but not as a string literal.
        If `has_dynamic_alias` is True, `alias` will be None.
        """
        expr = stmt.rvalue
        if isinstance(expr, TempNode):
            # TempNode means annotation-only
            return None, False

        if not (
            isinstance(expr, CallExpr) and isinstance(expr.callee, RefExpr) and expr.callee.fullname == FIELD_FULLNAME
        ):
            # Assigned value is not a call to pydantic.fields.Field
            return None, False

        for i, arg_name in enumerate(expr.arg_names):
            if arg_name != 'alias':
                continue
            arg = expr.args[i]
            if isinstance(arg, StrExpr):
                return arg.value, False
            else:
                return None, True
        return None, False

    def get_field_arguments(
        self, fields: List['PydanticModelField'], typed: bool, force_all_optional: bool, use_alias: bool
    ) -> List[Argument]:
        """
        Helper function used during the construction of the `__init__` and `construct` method signatures.

        Returns a list of mypy Argument instances for use in the generated signatures.
        """
        info = self._ctx.cls.info
        arguments = [
            field.to_argument(info, typed=typed, force_optional=force_all_optional, use_alias=use_alias)
            for field in fields
            if not (use_alias and field.has_dynamic_alias)
        ]
        return arguments

    def should_init_forbid_extra(self, fields: List['PydanticModelField'], config: 'ModelConfigData') -> bool:
        """
        Indicates whether the generated `__init__` should get a `**kwargs` at the end of its signature

        We disallow arbitrary kwargs if the extra config setting is "forbid", or if the plugin config says to,
        *unless* a required dynamic alias is present (since then we can't determine a valid signature).
        """
        if not config.allow_population_by_field_name:
            if self.is_dynamic_alias_present(fields, bool(config.has_alias_generator)):
                return False
        if config.forbid_extra:
            return True
        return self.plugin_config.init_forbid_extra

    @staticmethod
    def is_dynamic_alias_present(fields: List['PydanticModelField'], has_alias_generator: bool) -> bool:
        """
        Returns whether any fields on the model have a "dynamic alias", i.e., an alias that cannot be
        determined during static analysis.
        """
        for field in fields:
            if field.has_dynamic_alias:
                return True
        if has_alias_generator:
            for field in fields:
                if field.alias is None:
                    return True
        return False


class PydanticModelField:
    def __init__(
        self, name: str, is_required: bool, alias: Optional[str], has_dynamic_alias: bool, line: int, column: int
    ):
        self.name = name
        self.is_required = is_required
        self.alias = alias
        self.has_dynamic_alias = has_dynamic_alias
        self.line = line
        self.column = column

    def to_var(self, info: TypeInfo, use_alias: bool) -> Var:
        name = self.name
        if use_alias and self.alias is not None:
            name = self.alias
        return Var(name, info[self.name].type)

    def to_argument(self, info: TypeInfo, typed: bool, force_optional: bool, use_alias: bool) -> Argument:
        if typed and info[self.name].type is not None:
            type_annotation = info[self.name].type
        else:
            type_annotation = AnyType(TypeOfAny.explicit)
        return Argument(
            variable=self.to_var(info, use_alias),
            type_annotation=type_annotation,
            initializer=None,
            kind=ARG_NAMED_OPT if force_optional or not self.is_required else ARG_NAMED,
        )

    def serialize(self) -> JsonDict:
        return self.__dict__

    @classmethod
    def deserialize(cls, info: TypeInfo, data: JsonDict) -> 'PydanticModelField':
        return cls(**data)


class ModelConfigData:
    def __init__(
        self,
        forbid_extra: Optional[bool] = None,
        allow_mutation: Optional[bool] = None,
        frozen: Optional[bool] = None,
        orm_mode: Optional[bool] = None,
        allow_population_by_field_name: Optional[bool] = None,
        has_alias_generator: Optional[bool] = None,
    ):
        self.forbid_extra = forbid_extra
        self.allow_mutation = allow_mutation
        self.frozen = frozen
        self.orm_mode = orm_mode
        self.allow_population_by_field_name = allow_population_by_field_name
        self.has_alias_generator = has_alias_generator

    def set_values_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def update(self, config: Optional['ModelConfigData']) -> None:
        if config is None:
            return
        for k, v in config.set_values_dict().items():
            setattr(self, k, v)

    def setdefault(self, key: str, value: Any) -> None:
        if getattr(self, key) is None:
            setattr(self, key, value)


ERROR_ORM = ErrorCode('pydantic-orm', 'Invalid from_orm call', 'Pydantic')
ERROR_CONFIG = ErrorCode('pydantic-config', 'Invalid config value', 'Pydantic')
ERROR_ALIAS = ErrorCode('pydantic-alias', 'Dynamic alias disallowed', 'Pydantic')
ERROR_UNEXPECTED = ErrorCode('pydantic-unexpected', 'Unexpected behavior', 'Pydantic')
ERROR_UNTYPED = ErrorCode('pydantic-field', 'Untyped field disallowed', 'Pydantic')


def error_from_orm(model_name: str, api: CheckerPluginInterface, context: Context) -> None:
    api.fail(f'"{model_name}" does not have orm_mode=True', context, code=ERROR_ORM)


def error_invalid_config_value(name: str, api: SemanticAnalyzerPluginInterface, context: Context) -> None:
    api.fail(f'Invalid value for "Config.{name}"', context, code=ERROR_CONFIG)


def error_required_dynamic_aliases(api: SemanticAnalyzerPluginInterface, context: Context) -> None:
    api.fail('Required dynamic aliases disallowed', context, code=ERROR_ALIAS)


def error_unexpected_behavior(detail: str, api: CheckerPluginInterface, context: Context) -> None:  # pragma: no cover
    # Can't think of a good way to test this, but I confirmed it renders as desired by adding to a non-error path
    link = 'https://github.com/samuelcolvin/pydantic/issues/new/choose'
    full_message = f'The pydantic mypy plugin ran into unexpected behavior: {detail}\n'
    full_message += f'Please consider reporting this bug at {link} so we can try to fix it!'
    api.fail(full_message, context, code=ERROR_UNEXPECTED)


def error_untyped_fields(api: SemanticAnalyzerPluginInterface, context: Context) -> None:
    api.fail('Untyped fields disallowed', context, code=ERROR_UNTYPED)


def add_method(
    ctx: ClassDefContext,
    name: str,
    args: List[Argument],
    return_type: Type,
    self_type: Optional[Type] = None,
    tvar_def: Optional[TypeVarDef] = None,
    is_classmethod: bool = False,
    is_new: bool = False,
    # is_staticmethod: bool = False,
) -> None:
    """
    Adds a new method to a class.

    This can be dropped if/when https://github.com/python/mypy/issues/7301 is merged
    """
    info = ctx.cls.info

    # First remove any previously generated methods with the same name
    # to avoid clashes and problems in the semantic analyzer.
    if name in info.names:
        sym = info.names[name]
        if sym.plugin_generated and isinstance(sym.node, FuncDef):
            ctx.cls.defs.body.remove(sym.node)

    self_type = self_type or fill_typevars(info)
    if is_classmethod or is_new:
        first = [Argument(Var('_cls'), TypeType.make_normalized(self_type), None, ARG_POS)]
    # elif is_staticmethod:
    #     first = []
    else:
        self_type = self_type or fill_typevars(info)
        first = [Argument(Var('self'), self_type, None, ARG_POS)]
    args = first + args
    arg_types, arg_names, arg_kinds = [], [], []
    for arg in args:
        assert arg.type_annotation, 'All arguments must be fully typed.'
        arg_types.append(arg.type_annotation)
        arg_names.append(get_name(arg.variable))
        arg_kinds.append(arg.kind)

    function_type = ctx.api.named_type('__builtins__.function')
    signature = CallableType(arg_types, arg_kinds, arg_names, return_type, function_type)
    if tvar_def:
        signature.variables = [tvar_def]

    func = FuncDef(name, args, Block([PassStmt()]))
    func.info = info
    func.type = set_callable_name(signature, func)
    func.is_class = is_classmethod
    # func.is_static = is_staticmethod
    func._fullname = get_fullname(info) + '.' + name
    func.line = info.line

    # NOTE: we would like the plugin generated node to dominate, but we still
    # need to keep any existing definitions so they get semantically analyzed.
    if name in info.names:
        # Get a nice unique name instead.
        r_name = get_unique_redefinition_name(name, info.names)
        info.names[r_name] = info.names[name]

    if is_classmethod:  # or is_staticmethod:
        func.is_decorated = True
        v = Var(name, func.type)
        v.info = info
        v._fullname = func._fullname
        # if is_classmethod:
        v.is_classmethod = True
        dec = Decorator(func, [NameExpr('classmethod')], v)
        # else:
        #     v.is_staticmethod = True
        #     dec = Decorator(func, [NameExpr('staticmethod')], v)

        dec.line = info.line
        sym = SymbolTableNode(MDEF, dec)
    else:
        sym = SymbolTableNode(MDEF, func)
    sym.plugin_generated = True

    info.names[name] = sym
    info.defn.defs.body.append(func)


def get_fullname(x: Union[FuncBase, SymbolNode]) -> str:
    """
    Used for compatibility with mypy 0.740; can be dropped once support for 0.740 is dropped.
    """
    fn = x.fullname
    if callable(fn):  # pragma: no cover
        return fn()
    return fn


def get_name(x: Union[FuncBase, SymbolNode]) -> str:
    """
    Used for compatibility with mypy 0.740; can be dropped once support for 0.740 is dropped.
    """
    fn = x.name
    if callable(fn):  # pragma: no cover
        return fn()
    return fn
