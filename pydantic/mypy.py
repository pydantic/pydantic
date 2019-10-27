from collections import OrderedDict
from configparser import ConfigParser
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type as TypingType, TypeVar

from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_POS,
    ARG_STAR2,
    MDEF,
    Argument,
    AssignmentStmt,
    Block,
    CallExpr,
    ClassDef,
    Decorator,
    EllipsisExpr,
    FuncDef,
    JsonDict,
    MemberExpr,
    NameExpr,
    PassStmt,
    PlaceholderNode,
    RefExpr,
    StrExpr,
    SymbolTableNode,
    TempNode,
    TypeInfo,
    TypeVarExpr,
    Var,
)
from mypy.options import Options
from mypy.plugin import ClassDefContext, MethodContext, Plugin
from mypy.semanal import set_callable_name  # type: ignore
from mypy.server.trigger import make_wildcard_trigger
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    NoneTyp,
    Type,
    TypeOfAny,
    TypeType,
    TypeVarDef,
    TypeVarType,
    UnionType,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name

T = TypeVar('T')
CB = Optional[Callable[[T], None]]

PYDANTIC_PLUGIN_CONFIG_KEY = 'pydantic-mypy'
PYDANTIC_PLUGIN_METADATA_KEY = 'pydantic-mypy-metadata'
BASEMODEL_FULLNAME = 'pydantic.main.BaseModel'
SELF_TVAR_NAME = 'Model'


class ModelConfigData:
    def __init__(
        self,
        forbid_extra: bool = None,
        allow_mutation: bool = None,
        orm_mode: bool = None,
        allow_population_by_field_name: bool = None,
        has_alias_generator: bool = None,
    ):
        self.forbid_extra = forbid_extra
        self.allow_mutation = allow_mutation
        self.orm_mode = orm_mode
        self.allow_population_by_field_name = allow_population_by_field_name
        self.has_alias_generator = has_alias_generator

    def as_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def update(self, config: Optional['ModelConfigData']) -> None:
        if config is None:
            return
        for k, v in config.as_dict().items():
            setattr(self, k, v)

    def setdefault(self, key: str, value: Any) -> None:
        if getattr(self, key) is None:
            setattr(self, key, value)


class PydanticPluginConfig:
    allow_dynamic_aliases: bool
    allow_untyped_fields: bool
    init_allow_extra: bool
    init_typed: bool

    def __init__(self, options: Options) -> None:
        default_plugin_settings: Dict[str, bool] = dict(
            allow_dynamic_aliases=True, allow_untyped_fields=True, init_allow_extra=True, init_typed=False
        )
        if options.config_file is not None:
            plugin_config = ConfigParser()
            plugin_config.read(options.config_file)
            for key, default in default_plugin_settings.items():
                setting = plugin_config.getboolean(PYDANTIC_PLUGIN_CONFIG_KEY, key, fallback=default)
                if setting is not None:
                    setattr(self, key, setting)


class PydanticPlugin(Plugin):
    def __init__(self, options: Options) -> None:
        self.plugin_config = PydanticPluginConfig(options)
        super().__init__(options)

    def get_method_hook(self, fullname: str) -> Optional[Callable[[MethodContext], Type]]:
        if fullname.endswith('.from_orm'):
            return from_orm_callback
        return None

    def get_base_class_hook(self, fullname: str) -> 'CB[ClassDefContext]':
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            if is_pydantic_model(sym.node):
                return partial(pydantic_model_class_maker_callback, plugin_config=self.plugin_config)
        return None


def is_pydantic_model(info: TypeInfo) -> bool:
    for base in info.mro:
        if base.fullname() == BASEMODEL_FULLNAME:
            return True
    return False


class PydanticModelField:
    def __init__(
        self, name: str, is_required: bool, alias: Optional[str], has_dynamic_alias: bool, line: int, column: int
    ) -> None:
        self.name = name
        self.is_required = is_required
        self.alias = alias
        self.has_dynamic_alias = has_dynamic_alias
        self.line = line
        self.column = column

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

    def to_var(self, info: TypeInfo, use_alias: bool) -> Var:
        name = self.name
        if use_alias and self.alias is not None:
            name = self.alias
        return Var(name, info[self.name].type)

    def serialize(self) -> JsonDict:
        return {
            'name': self.name,
            'is_required': self.is_required,
            'alias': self.alias,
            'has_dynamic_alias': self.has_dynamic_alias,
            'line': self.line,
            'column': self.column,
        }

    @classmethod
    def deserialize(cls, info: TypeInfo, data: JsonDict) -> 'PydanticModelField':
        return cls(**data)


class PydanticModelTransformer:
    _fields_set_argument: Optional[Argument] = None

    def __init__(self, ctx: ClassDefContext, plugin_config: PydanticPluginConfig) -> None:
        self._ctx = ctx
        self.plugin_config = plugin_config
        self.model_config_fields = {
            'extra',
            'allow_mutation',
            'orm_mode',
            'allow_population_by_field_name',
            'alias_generator',
        }

    def transform(self) -> None:
        ctx = self._ctx
        info = self._ctx.cls.info

        config = self.collect_config()
        attributes = self.collect_fields()
        for attr in attributes:
            if info[attr.name].type is None:
                if not ctx.api.final_iteration:
                    ctx.api.defer()

        is_settings = self.is_settings()
        self.add_initializer(attributes, config, is_settings)
        self.add_construct_method(attributes, is_settings)
        if config.allow_mutation is False:
            self._set_frozen(attributes, frozen=True)
        else:
            self._set_frozen(attributes, frozen=False)

        info.metadata[PYDANTIC_PLUGIN_METADATA_KEY] = {
            'attributes': OrderedDict((attr.name, attr.serialize()) for attr in attributes),
            'config': config.as_dict(),
            'is_settings': is_settings,
        }

    def is_settings(self) -> bool:
        for info in self._ctx.cls.info.mro[:-1]:  # 0 is the current class, -1 is object
            if info.fullname() == 'pydantic.env_settings.BaseSettings':
                return True
        return False

    def collect_config(self) -> ModelConfigData:
        ctx = self._ctx
        cls = ctx.cls
        config = ModelConfigData()
        for stmt in cls.defs.body:
            if not isinstance(stmt, ClassDef):
                continue
            if stmt.name != 'Config':
                continue
            for substmt in stmt.defs.body:
                if not isinstance(substmt, AssignmentStmt):
                    continue
                config.update(self.get_config_update(substmt))
        for info in cls.info.mro[1:]:  # 0 is the current class
            if PYDANTIC_PLUGIN_METADATA_KEY not in info.metadata:
                continue

            # Each class depends on the set of attributes in its ancestors
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname()))

            for name, value in info.metadata[PYDANTIC_PLUGIN_METADATA_KEY]['config'].items():
                config.setdefault(name, value)
        return config

    def collect_fields(self) -> List[PydanticModelField]:
        # First, collect attributes belonging to the current class.
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

            if not stmt.new_syntax and not self.plugin_config.allow_untyped_fields:
                ctx.api.fail('Untyped fields not allowed by plugin config [pydantic]', stmt)

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
            assert isinstance(node, Var)

            # x: ClassVar[int] is ignored by dataclasses.
            if node.is_classvar:
                continue

            is_required = self._get_is_required(cls, stmt, lhs)
            alias, has_dynamic_alias = self._get_alias_info(stmt)
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
        all_attrs = fields.copy()
        for info in cls.info.mro[1:]:  # 0 is the current class, -2 is BaseModel, -1 is object
            if PYDANTIC_PLUGIN_METADATA_KEY not in info.metadata:
                continue

            super_attrs = []
            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname()))

            for name, data in info.metadata[PYDANTIC_PLUGIN_METADATA_KEY]['attributes'].items():
                if name not in known_fields:
                    attr = PydanticModelField.deserialize(info, data)
                    known_fields.add(name)
                    super_attrs.append(attr)
                else:
                    (attr,) = [a for a in all_attrs if a.name == name]
                    all_attrs.remove(attr)
                    super_attrs.append(attr)
            all_attrs = super_attrs + all_attrs
        return all_attrs

    def get_field_arguments(
        self, fields: List[PydanticModelField], typed: bool, force_all_optional: bool, use_alias: bool
    ) -> List[Argument]:
        info = self._ctx.cls.info
        arguments = [
            field.to_argument(info, typed=typed, force_optional=force_all_optional, use_alias=use_alias)
            for field in fields
            if not (use_alias and field.has_dynamic_alias)
        ]
        return arguments

    def get_fields_set_argument(self) -> Optional[Argument]:
        # TODO: Actually construct the _fields_set_argument, rather than ripping it off of BaseModel
        # Use a debugger to get the details, then build it
        if self._fields_set_argument is None:
            for cls in self._ctx.cls.info.mro:
                if cls.fullname() == BASEMODEL_FULLNAME:
                    construct_method_type = cls.names['construct'].type
                    break
            else:  # pragma: no cover
                # Can't reproduce, but this branch seems to need handling intermittently
                if not self._ctx.api.final_iteration:
                    self._ctx.api.defer()
                return None
            if not isinstance(construct_method_type, CallableType):
                return None  # fails for uninherited BaseSettings for some reason
            arg_name = '_fields_set'
            arg_index = construct_method_type.arg_names.index(arg_name)
            arg_kind = construct_method_type.arg_kinds[arg_index]
            arg_type = construct_method_type.arg_types[arg_index]
            variable = Var(arg_name, arg_type)
            argument = Argument(variable, arg_type, None, arg_kind)
            type(self)._fields_set_argument = argument
        return self._fields_set_argument

    def add_extra(self, fields: List[PydanticModelField], config: ModelConfigData) -> bool:
        if not config.allow_population_by_field_name:
            if any(field.has_dynamic_alias for field in fields):
                return True
            if config.has_alias_generator and any(field.alias is None for field in fields):
                return True
        if config.forbid_extra:
            return False
        return self.plugin_config.init_allow_extra

    def add_initializer(self, fields: List[PydanticModelField], config: ModelConfigData, is_settings: bool) -> None:
        ctx = self._ctx
        typed = self.plugin_config.init_typed
        use_alias = config.allow_population_by_field_name is not True
        force_all_optional = is_settings or bool(
            config.has_alias_generator and not config.allow_population_by_field_name
        )
        init_arguments = self.get_field_arguments(
            fields, typed=typed, force_all_optional=force_all_optional, use_alias=use_alias
        )
        if self.add_extra(fields, config):
            var = Var('kwargs')
            init_arguments.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))
        add_method(ctx, '__init__', init_arguments, NoneTyp())

    def add_construct_method(self, fields: List[PydanticModelField], is_settings: bool) -> None:
        fields_set_argument = self.get_fields_set_argument()
        if fields_set_argument is None:
            return
        ctx = self._ctx
        construct_arguments = self.get_field_arguments(
            fields, typed=True, force_all_optional=is_settings, use_alias=False
        )
        construct_arguments = [fields_set_argument] + construct_arguments

        obj_type = ctx.api.named_type('__builtins__.object')
        tvar_fullname = ctx.cls.fullname + '.' + SELF_TVAR_NAME
        tvd = TypeVarDef(SELF_TVAR_NAME, tvar_fullname, -1, [], obj_type)
        self_tvar_expr = TypeVarExpr(SELF_TVAR_NAME, tvar_fullname, [], obj_type)
        ctx.cls.info.names[SELF_TVAR_NAME] = SymbolTableNode(MDEF, self_tvar_expr)
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

    def get_config_update(self, substmt: AssignmentStmt) -> Optional[ModelConfigData]:
        lhs = substmt.lvalues[0]
        if not (isinstance(lhs, NameExpr) and lhs.name in self.model_config_fields):
            return None
        if lhs.name == 'extra':
            if isinstance(substmt.rvalue, StrExpr):
                forbid_extra = substmt.rvalue.value == 'forbid'
            elif isinstance(substmt.rvalue, MemberExpr):
                forbid_extra = substmt.rvalue.name == 'forbid'
            else:
                self.error_invalid_config_value(lhs.name, substmt)
                return None
            return ModelConfigData(forbid_extra=forbid_extra)
        if lhs.name == 'alias_generator':
            # TODO: trigger an error if appropriate based on plugin config
            # TODO: Check if the value set is actually just None
            # alias_generator = substmt.rvalue.value
            return ModelConfigData(has_alias_generator=True)
        if isinstance(substmt.rvalue, NameExpr) and substmt.rvalue.fullname in ('builtins.True', 'builtins.False'):
            return ModelConfigData(**{lhs.name: substmt.rvalue.fullname == 'builtins.True'})
        self.error_invalid_config_value(lhs.name, substmt)
        return None

    def error_invalid_config_value(self, lhs_name: str, stmt: AssignmentStmt) -> None:
        self._ctx.api.fail(f'Invalid value specified for "Config.{lhs_name}" [pydantic]', stmt)

    @staticmethod
    def _get_alias_info(stmt: AssignmentStmt) -> Tuple[Optional[str], bool]:
        expr = stmt.rvalue
        if isinstance(expr, TempNode):
            # I believe TempNode means annotation-only
            return None, False

        if not (
            isinstance(expr, CallExpr)
            and isinstance(expr.callee, RefExpr)
            and expr.callee.fullname == 'pydantic.fields.Field'
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

    @staticmethod
    def _get_is_required(cls: ClassDef, stmt: AssignmentStmt, lhs: NameExpr) -> bool:
        expr = stmt.rvalue
        if not isinstance(expr, TempNode):
            if (
                isinstance(expr, CallExpr)
                and isinstance(expr.callee, RefExpr)
                and expr.callee.fullname == 'pydantic.fields.Field'
            ):
                arg_is_ellipsis = len(expr.args) > 0 and type(expr.args[0]) is EllipsisExpr
            else:
                arg_is_ellipsis = isinstance(expr, EllipsisExpr)
            return arg_is_ellipsis
        # I believe TempNode means annotation-only
        value_type = cls.info[lhs.name].type
        if type(value_type) is UnionType:
            item_types = [type(item) for item in value_type.items]  # type: ignore
            if NoneTyp in item_types:
                return False
        return True

    def _set_frozen(self, attributes: List[PydanticModelField], frozen: bool) -> None:
        info = self._ctx.cls.info
        for attr in attributes:
            sym_node = info.names.get(attr.name)
            if sym_node is not None:
                var = sym_node.node
                assert isinstance(var, Var)
                var.is_property = frozen
            else:
                var = attr.to_var(info, use_alias=False)
                var.info = info
                var.is_property = frozen
                var._fullname = info.fullname() + '.' + var.name()
                info.names[var.name()] = SymbolTableNode(MDEF, var)


def pydantic_model_class_maker_callback(ctx: ClassDefContext, plugin_config: PydanticPluginConfig) -> None:
    transformer = PydanticModelTransformer(ctx, plugin_config)
    transformer.transform()


def from_orm_callback(ctx: MethodContext) -> Type:
    """Raise an error if orm_mode is not enabled"""
    if isinstance(ctx.type, CallableType):
        model_type = ctx.type.ret_type  # called on the class
    elif isinstance(ctx.type, Instance):
        model_type = ctx.type  # called on an instance (unusual, but still valid)
    else:  # pragma: no cover
        # Not sure if there is any way to get to this branch, but better to fail gracefully
        return ctx.default_return_type
    type_info = model_type.type  # type: ignore
    orm_mode = type_info.metadata.get(PYDANTIC_PLUGIN_METADATA_KEY, {}).get('config', {}).get('orm_mode')
    if orm_mode is not True:
        ctx.api.fail(f'"{type_info.name()}" does not have orm_mode=True in its Config [pydantic]', ctx.context)
    return ctx.default_return_type


def plugin(version: str) -> 'TypingType[Plugin]':
    return PydanticPlugin


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
    """Adds a new method to a class.

    This can be dropped once https://github.com/python/mypy/issues/7301 is merged
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
        arg_names.append(arg.variable.name())
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
    func._fullname = info.fullname() + '.' + name
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
