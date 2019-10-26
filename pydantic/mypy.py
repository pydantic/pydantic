from collections import OrderedDict
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Type as TypingType, TypeVar

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
from mypy.plugin import ClassDefContext, MethodContext, Plugin
from mypy.semanal import set_callable_name
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

BASEMODEL_NAME = 'pydantic.main.BaseModel'
SELF_TVAR_NAME = "_BMT"  # type: Final


class PydanticPlugin(Plugin):
    pydantic_strict: bool = False

    def get_method_hook(self, fullname: str) -> Optional[Callable[[MethodContext], Type]]:
        if fullname.endswith(".from_orm"):
            return from_orm_callback

    def get_base_class_hook(self, fullname: str) -> 'CB[ClassDefContext]':
        # This function is called on any class that is the base class for another class
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            if is_model(sym.node):
                return partial(pydantic_model_class_maker_callback, strict=self.pydantic_strict)
        return None


class StrictPydanticPlugin(PydanticPlugin):
    pydantic_strict: bool = True


def is_model(info: TypeInfo) -> bool:
    for base in info.mro:
        if base.fullname() == BASEMODEL_NAME:
            return True
    return False


class PydanticModelField:
    def __init__(self, name: str, has_default: bool, line: int, column: int) -> None:
        self.name = name
        self.has_default = has_default
        self.line = line
        self.column = column

    def to_argument(self, info: TypeInfo, typed: bool, for_settings: bool) -> Argument:
        if typed and info[self.name].type is not None:
            type_annotation = info[self.name].type
        else:
            type_annotation = AnyType(TypeOfAny.explicit)
        return Argument(
            variable=self.to_var(info),
            type_annotation=type_annotation,
            initializer=None,
            kind=ARG_NAMED_OPT if self.has_default or for_settings else ARG_NAMED,
        )

    def to_var(self, info: TypeInfo) -> Var:
        return Var(self.name, info[self.name].type)

    def serialize(self) -> JsonDict:
        return {'name': self.name, 'has_default': self.has_default, 'line': self.line, 'column': self.column}

    @classmethod
    def deserialize(cls, info: TypeInfo, data: JsonDict) -> 'PydanticModelField':
        return cls(**data)


class PydanticModelTransformer:
    _fields_set_argument: Optional[Argument] = None

    def __init__(self, ctx: ClassDefContext, strict: bool) -> None:
        self._ctx = ctx
        self.config_fields = ('extra', 'allow_mutation', 'orm_mode')
        self.strict = strict

    def get_initializer_arguments(
        self, attributes: List[PydanticModelField], typed: bool, is_settings: bool
    ) -> List[Argument]:
        info = self._ctx.cls.info
        arguments = [attribute.to_argument(info, typed=typed, for_settings=is_settings) for attribute in attributes]
        return arguments

    def get_fields_set_argument(self) -> Optional[Argument]:
        if self._fields_set_argument is None:
            for cls in self._ctx.cls.info.mro:
                if cls.fullname() == BASEMODEL_NAME:
                    construct_method_type = cls.names['construct'].type
                    break
            else:  # pragma: no cover
                # Can't reproduce, but this branch seems to need handling intermittently
                if not self._ctx.api.final_iteration:
                    self._ctx.api.defer()
                return None
            if not isinstance(construct_method_type, CallableType):
                return  # fails for uninherited BaseSettings for some reason
            arg_kind = construct_method_type.arg_kinds[1]
            arg_name = construct_method_type.arg_names[1]
            arg_type = construct_method_type.arg_types[1]
            variable = Var(arg_name, arg_type)
            argument = Argument(variable, arg_type, None, arg_kind)
            type(self)._fields_set_argument = argument
        return self._fields_set_argument

    def add_construct(self, attributes: List[PydanticModelField], is_settings: bool) -> None:
        fields_set_argument = self.get_fields_set_argument()
        if fields_set_argument is None:
            return
        ctx = self._ctx
        construct_arguments = self.get_initializer_arguments(attributes, typed=True, is_settings=is_settings)
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

    def add_initializer(self, attributes: List[PydanticModelField], config: Dict[str, Any], is_settings: bool) -> None:
        ctx = self._ctx
        init_arguments = self.get_initializer_arguments(attributes, typed=self.strict, is_settings=is_settings)
        if config.get('extra') is not False and not self.strict:
            var = Var('kwargs')
            init_arguments.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))
        add_method(ctx, '__init__', init_arguments, NoneTyp())

    def transform(self) -> None:
        ctx = self._ctx
        info = self._ctx.cls.info

        attributes = self.collect_attributes()
        config = self.collect_config()
        is_settings = self.is_settings()

        for attr in attributes:
            if info[attr.name].type is None:
                if not ctx.api.final_iteration:
                    ctx.api.defer()

        self.add_initializer(attributes, config, is_settings)
        self.add_construct(attributes, is_settings)
        if config.get('allow_mutation') is False:
            self._set_frozen(attributes, frozen=True)
        else:
            self._set_frozen(attributes, frozen=False)

        info.metadata['pydanticmodel'] = {
            'attributes': OrderedDict((attr.name, attr.serialize()) for attr in attributes),
            'config': config,
            'is_settings': is_settings,
        }

    def collect_config(self) -> Dict[str, Any]:
        ctx = self._ctx
        cls = ctx.cls
        config = {}
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
            if 'pydanticmodel' not in info.metadata:
                continue

            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname()))

            for name, value in info.metadata['pydanticmodel']['config'].items():
                if name not in config:
                    config[name] = value
        return config

    def is_settings(self) -> bool:
        for info in self._ctx.cls.info.mro[:-1]:  # 0 is the current class, -1 is object
            if info.fullname() == 'pydantic.env_settings.BaseSettings':
                return True
        return False

    def get_config_update(self, substmt: AssignmentStmt) -> Dict[str, Any]:
        lhs = substmt.lvalues[0]
        if not (isinstance(lhs, NameExpr) and lhs.name in self.config_fields):
            return {}
        if lhs.name == 'extra':
            if isinstance(substmt.rvalue, StrExpr):
                extra_value = substmt.rvalue.value != 'forbid'
            elif isinstance(substmt.rvalue, MemberExpr):
                extra_value = substmt.rvalue.name != 'forbid'
            else:
                self.error_invalid_config_value(lhs.name, substmt)
                return {}
            return {lhs.name: extra_value}
        if isinstance(substmt.rvalue, NameExpr) and substmt.rvalue.fullname in ('builtins.True', 'builtins.False'):
            return {lhs.name: substmt.rvalue.fullname == 'builtins.True'}
        self.error_invalid_config_value(lhs.name, substmt)
        return {}

    def error_invalid_config_value(self, lhs_name: str, stmt: AssignmentStmt) -> None:
        self._ctx.api.fail(f'Invalid value specified for "Config.{lhs_name}" [pydantic]', stmt)

    def collect_attributes(self) -> List[PydanticModelField]:
        # First, collect attributes belonging to the current class.
        ctx = self._ctx
        cls = self._ctx.cls
        attrs = []  # type: List[PydanticModelField]
        known_attrs = set()  # type: Set[str]
        for stmt in cls.defs.body:

            if not isinstance(stmt, AssignmentStmt):  # `and stmt.new_syntax` to require annotation
                continue

            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                continue

            if lhs.name == '__config__':  # BaseConfig not well handled; I'm not sure why yet
                continue

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

            has_default = self._get_has_default(cls, stmt, lhs)
            known_attrs.add(lhs.name)
            attrs.append(PydanticModelField(name=lhs.name, has_default=has_default, line=stmt.line, column=stmt.column))
        all_attrs = attrs.copy()
        for info in cls.info.mro[1:]:  # 0 is the current class, -2 is BaseModel, -1 is object
            if 'pydanticmodel' not in info.metadata:
                continue

            super_attrs = []
            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname()))

            for name, data in info.metadata['pydanticmodel']['attributes'].items():
                if name not in known_attrs:
                    attr = PydanticModelField.deserialize(info, data)
                    known_attrs.add(name)
                    super_attrs.append(attr)
                else:
                    (attr,) = [a for a in all_attrs if a.name == name]
                    all_attrs.remove(attr)
                    super_attrs.append(attr)
            all_attrs = super_attrs + all_attrs
        return all_attrs

    def _get_has_default(self, cls: ClassDef, stmt: AssignmentStmt, lhs: NameExpr) -> bool:
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
            return not arg_is_ellipsis
        value_type = cls.info[lhs.name].type
        if type(value_type) is UnionType:
            item_types = [type(item) for item in value_type.items]  # type: ignore
            if NoneTyp in item_types:
                return True
        return False

    def _set_frozen(self, attributes: List[PydanticModelField], frozen: bool) -> None:
        info = self._ctx.cls.info
        for attr in attributes:
            sym_node = info.names.get(attr.name)
            if sym_node is not None:
                var = sym_node.node
                assert isinstance(var, Var)
                var.is_property = frozen
            else:
                var = attr.to_var(info)
                var.info = info
                var.is_property = frozen
                var._fullname = info.fullname() + '.' + var.name()
                info.names[var.name()] = SymbolTableNode(MDEF, var)


def pydantic_model_class_maker_callback(ctx: ClassDefContext, strict: bool) -> None:
    transformer = PydanticModelTransformer(ctx, strict)
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
    orm_mode = model_type.type.metadata.get('pydanticmodel', {}).get('config', {}).get('orm_mode')
    if orm_mode is not True:
        ctx.api.fail(f'"{model_type.type.name()}" does not have orm_mode=True in its Config [pydantic]', ctx.context)
    return ctx.default_return_type


def plugin(version: str) -> 'TypingType[Plugin]':
    return PydanticPlugin


def strict(version: str) -> 'TypingType[Plugin]':
    return StrictPydanticPlugin


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

    if is_classmethod:  #  or is_staticmethod:
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
