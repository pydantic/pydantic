//! Attribute access on Pydantic model classes, in C API terms:
//!
//! - `_install_model_metaclass_getattro(ModelMetaclass)`, setting -- on that exact (heap) type object -- the
//!   attribute access slot to a C function equivalent to what CPython's generic slot does for a metaclass
//!   defining `__getattr__()` in Python (`type.__getattribute__()`, then for missing attributes the fallback on
//!   the model private attributes that `ModelMetaclass.__getattr__()` implements), see
//!   `model_metaclass_getattro()` and `install_model_metaclass_getattro()`.
//! - `_model_class_getattr(cls, name, default)` / `_model_class_hasattr(cls, name)`, the equivalents of the
//!   `getattr()`/`hasattr()` builtins for such classes used by `pydantic._internal._fields`, which don't involve
//!   any exception for missing attributes (thousands of such lookups, mostly misses, happen during models creation
//!   and schema generation). These are raw `METH_FASTCALL` functions.
//!
//! For these functions, whether the name is present at all (in the MRO of the class or of its metaclass, which is
//! what `type.__getattribute__()` looks at) is first checked without raising anything; if present,
//! `type.__getattribute__()` is used to get the value (so that descriptors, metaclass attributes, etc. are handled
//! exactly as usual); if not, or if that raised an `AttributeError`, the private attributes fallback is applied.
//!
//! Pure Python versions of these are used as a fallback on other Python implementations.
use std::ffi::c_void;
use std::sync::atomic::{AtomicPtr, Ordering};

use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::types::PyModule;

unsafe extern "C" {
    // Declared in `Include/cpython/object.h` (not exposed by `pyo3-ffi`): looks up a name in the MRO of a type
    // (through the type attribute cache), without invoking descriptors and without setting an exception.
    // Returns a borrowed reference, or null if the name isn't present.
    fn _PyType_Lookup(tp: *mut ffi::PyTypeObject, name: *mut ffi::PyObject) -> *mut ffi::PyObject;
}

/// The interned `'__private_attributes__'` string (set when the objects are created, lives forever).
static PRIVATE_ATTRIBUTES_STR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());

/// The interned `'__dict__'` string (set when the objects are created, lives forever).
static DICT_STR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());

/// The `__dict__` descriptor of `type` (i.e. `type.__dict__['__dict__']`, a borrowed reference living forever).
static TYPE_DICT_DESCRIPTOR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());

/// The class' own `__dict__` (borrowed), or null.
#[inline]
unsafe fn type_own_dict(cls: *mut ffi::PyTypeObject) -> *mut ffi::PyObject {
    unsafe {
        let dict = (*cls).tp_dict;
        #[cfg(Py_3_12)]
        if dict.is_null() {
            // Static builtin types (never the case for the classes these functions are meant for):
            let dict = ffi::PyType_GetDict(cls);
            if !dict.is_null() {
                // The type holds a reference to it.
                ffi::Py_DECREF(dict);
            }
            return dict;
        }
        dict
    }
}

/// The private attributes fallback: `cls.__dict__.get('__private_attributes__')`, and if truthy and containing
/// `name`, its `name` item (new reference); `Ok(null)` if there is no such private attribute (no exception set),
/// `Err(())` if an exception is set.
///
/// Python equivalent (the `__getattr__()` method of `ModelMetaclass`, minus the final `raise`):
///
/// ```python
/// def __getattr__(self, item: str) -> Any:
///     """This is necessary to keep attribute access working for class attribute access."""
///     private_attributes = self.__dict__.get('__private_attributes__')
///     if private_attributes and item in private_attributes:
///         return private_attributes[item]
///     raise AttributeError(item)
/// ```
unsafe fn private_attribute(cls: *mut ffi::PyTypeObject, name: *mut ffi::PyObject) -> Result<*mut ffi::PyObject, ()> {
    unsafe {
        let dict = type_own_dict(cls);
        if dict.is_null() {
            return Ok(std::ptr::null_mut());
        }
        // (a strong reference, as arbitrary code can run below)
        let mut private_attributes: *mut ffi::PyObject = std::ptr::null_mut();
        match ffi::compat::PyDict_GetItemRef(
            dict,
            PRIVATE_ATTRIBUTES_STR.load(Ordering::Relaxed),
            &raw mut private_attributes,
        ) {
            -1 => return Err(()),
            0 => return Ok(std::ptr::null_mut()),
            _ => {}
        }
        let result = match ffi::PyObject_IsTrue(private_attributes) {
            -1 => Err(()),
            0 => Ok(std::ptr::null_mut()),
            _ => match ffi::PySequence_Contains(private_attributes, name) {
                -1 => Err(()),
                0 => Ok(std::ptr::null_mut()),
                _ => {
                    let item = ffi::PyObject_GetItem(private_attributes, name);
                    if item.is_null() { Err(()) } else { Ok(item) }
                }
            },
        };
        ffi::Py_DECREF(private_attributes);
        result
    }
}

/// `type.__getattribute__(cls, name)` with the private attributes fallback: returns a new reference to the
/// attribute value, `Ok(null)` if it is missing (no exception set), or `Err(())` if an exception (other than
/// the handled `AttributeError`) is set. `cls` must be a type object.
unsafe fn lookup(cls: *mut ffi::PyObject, name: *mut ffi::PyObject) -> Result<*mut ffi::PyObject, ()> {
    unsafe {
        // SAFETY: `PyType_Type` is a valid static type object, whose `tp_getattro` slot (`type.__getattribute__`)
        // is always set.
        let type_getattro = (*std::ptr::addr_of!(ffi::PyType_Type)).tp_getattro.unwrap();
        if ffi::PyUnicode_Check(name) == 0 {
            // Let `type.__getattribute__()` raise the appropriate `TypeError`:
            let res = type_getattro(cls, name);
            return if res.is_null() { Err(()) } else { Ok(res) };
        }

        let cls_type = cls.cast::<ffi::PyTypeObject>();
        // `type.__getattribute__(cls, name)` raises an `AttributeError` (of its own) if and only if the name is
        // found neither in the MRO of the metaclass nor in the MRO of the class; knowing this in advance avoids
        // the cost of an exception (and of formatting its message) for nothing:
        let present = !_PyType_Lookup(ffi::Py_TYPE(cls), name).is_null() || !_PyType_Lookup(cls_type, name).is_null();
        if present {
            let res = type_getattro(cls, name);
            if !res.is_null() {
                return Ok(res);
            }
            // (this can still be an `AttributeError`, e.g. raised by a descriptor)
            if ffi::PyErr_ExceptionMatches(ffi::PyExc_AttributeError) == 0 {
                return Err(());
            }
            ffi::PyErr_Clear();
        }
        private_attribute(cls_type, name)
    }
}

/// The `tp_getattro` slot installed on `ModelMetaclass` by `install_model_metaclass_getattro()`, i.e. attribute
/// access on model classes: equivalent to `type.__getattribute__()` followed -- for missing attributes -- by the
/// `__getattr__()` shown above.
///
/// Defining `__getattr__()` in Python on a metaclass makes CPython route *every* attribute access on its classes
/// through a generic slot function (`slot_tp_getattr_hook`), calling `type.__getattribute__()` through a temporary
/// method wrapper object and -- for missing attributes -- formatting and raising an `AttributeError`, clearing it,
/// calling `__getattr__()` (a Python frame) and raising again: about 5 and 10 times the cost of the same operations
/// on a plain class. With this slot, present attributes only pay for `type.__getattribute__()`, and missing ones
/// don't involve any Python frame. The `AttributeError` of a miss is the same (`AttributeError(name)`, given the
/// `name`/`obj` context by the interpreter as for one raised by `__getattr__()`).
unsafe extern "C" fn model_metaclass_getattro(cls: *mut ffi::PyObject, name: *mut ffi::PyObject) -> *mut ffi::PyObject {
    unsafe {
        // SAFETY: `PyType_Type` is a valid static type object, whose `tp_getattro` slot (`type.__getattribute__`)
        // is always set.
        let type_getattro = (*std::ptr::addr_of!(ffi::PyType_Type)).tp_getattro.unwrap();
        // Unlike in `lookup()`, no check for the presence of the name first: through this slot (plain attribute
        // accesses on model classes), present attributes are by far the most common.
        let res = type_getattro(cls, name);
        if !res.is_null() || ffi::PyErr_ExceptionMatches(ffi::PyExc_AttributeError) == 0 {
            return res;
        }
        ffi::PyErr_Clear();
        match private_attribute(cls.cast::<ffi::PyTypeObject>(), name) {
            Err(()) => std::ptr::null_mut(),
            Ok(res) if !res.is_null() => res,
            Ok(_) => {
                // `raise AttributeError(item)`:
                ffi::PyErr_SetObject(ffi::PyExc_AttributeError, name);
                std::ptr::null_mut()
            }
        }
    }
}

/// The type check of the `cls` argument of the functions (with the error `type.__getattribute__(cls, name)` raises).
#[inline]
unsafe fn check_type_argument(cls: *mut ffi::PyObject) -> bool {
    unsafe {
        if ffi::PyType_Check(cls) == 0 {
            ffi::PyErr_Format(
                ffi::PyExc_TypeError,
                c"descriptor '__getattribute__' requires a 'type' object but received a '%.100s'".as_ptr(),
                (*ffi::Py_TYPE(cls)).tp_name,
            );
            return false;
        }
        true
    }
}

/// `_model_class_getattr(cls, name, default, /)`
unsafe extern "C" fn model_class_getattr_fastcall(
    _self: *mut ffi::PyObject,
    args: *mut *mut ffi::PyObject,
    nargs: ffi::Py_ssize_t,
) -> *mut ffi::PyObject {
    unsafe {
        if nargs != 3 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_model_class_getattr() takes exactly 3 positional arguments".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        if !check_type_argument(*args) {
            return std::ptr::null_mut();
        }
        match lookup(*args, *args.add(1)) {
            Err(()) => std::ptr::null_mut(),
            Ok(res) if res.is_null() => {
                let default = *args.add(2);
                ffi::Py_INCREF(default);
                default
            }
            Ok(res) => res,
        }
    }
}

/// `_model_class_hasattr(cls, name, /)`
unsafe extern "C" fn model_class_hasattr_fastcall(
    _self: *mut ffi::PyObject,
    args: *mut *mut ffi::PyObject,
    nargs: ffi::Py_ssize_t,
) -> *mut ffi::PyObject {
    unsafe {
        if nargs != 2 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_model_class_hasattr() takes exactly 2 positional arguments".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        if !check_type_argument(*args) {
            return std::ptr::null_mut();
        }
        match lookup(*args, *args.add(1)) {
            Err(()) => std::ptr::null_mut(),
            Ok(res) => {
                let found = !res.is_null();
                if found {
                    ffi::Py_DECREF(res);
                }
                let result = if found { ffi::Py_True() } else { ffi::Py_False() };
                ffi::Py_INCREF(result);
                result
            }
        }
    }
}

/// Whether `cls.__dict__` (and `vars(cls)`) is known to be the read-only proxy of the class' own namespace, as
/// for any class whose metaclass doesn't customize attribute accesses nor `__dict__`: the attribute is then the
/// `__dict__` data descriptor of `type` found through the standard `type.__getattribute__()` -- either as the slot
/// itself, or through `model_metaclass_getattro()`, or through CPython's generic slot for a metaclass having a
/// Python `__getattr__()` in its MRO (as long as `__getattribute__` is `type`'s: a data descriptor of the metaclass
/// is then found before `__getattr__()` could be involved).
#[inline]
pub(crate) unsafe fn has_standard_type_dict(cls: *mut ffi::PyObject) -> bool {
    unsafe {
        let metatype = ffi::Py_TYPE(cls);
        let getattro = getattro_pointer(metatype);
        if getattro != TYPE_GETATTRO.load(Ordering::Relaxed) && getattro != model_metaclass_getattro as *mut c_void {
            let generic_hook = GENERIC_GETATTR_HOOK.load(Ordering::Relaxed);
            if generic_hook.is_null()
                || getattro != generic_hook
                || _PyType_Lookup(metatype, GETATTRIBUTE_STR.load(Ordering::Relaxed))
                    != TYPE_GETATTRIBUTE_DESCRIPTOR.load(Ordering::Relaxed)
            {
                return false;
            }
        }
        _PyType_Lookup(metatype, DICT_STR.load(Ordering::Relaxed)) == TYPE_DICT_DESCRIPTOR.load(Ordering::Relaxed)
    }
}

/// The `tp_getattro` slot of a type, as an untyped pointer (null if unset).
#[inline]
unsafe fn getattro_pointer(tp: *mut ffi::PyTypeObject) -> *mut c_void {
    unsafe {
        match (*tp).tp_getattro {
            Some(f) => f as *mut c_void,
            None => std::ptr::null_mut(),
        }
    }
}

/// The attribute access slot function of `type` (`type.__getattribute__`, as set on the type object).
static TYPE_GETATTRO: AtomicPtr<c_void> = AtomicPtr::new(std::ptr::null_mut());

/// CPython's generic attribute access slot function for types having a Python `__getattr__()` in their MRO
/// (`slot_tp_getattr_hook`, not exposed by the C API): recorded by `install_model_metaclass_getattro()` from the
/// metaclass it is applied to, null until then.
static GENERIC_GETATTR_HOOK: AtomicPtr<c_void> = AtomicPtr::new(std::ptr::null_mut());

/// The interned `'__getattr__'`/`'__getattribute__'` strings (set when the objects are created, live forever).
static GETATTR_STR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());
static GETATTRIBUTE_STR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());

/// The `__getattribute__` descriptor of `type` (i.e. `type.__dict__['__getattribute__']`, the slot wrapper of
/// `type.__getattribute__`; a borrowed reference living forever).
static TYPE_GETATTRIBUTE_DESCRIPTOR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());

/// `_install_model_metaclass_getattro(metaclass, /)`: make `model_metaclass_getattro()` the attribute access
/// slot (`tp_getattro`) of *that exact type object*, Pydantic's `ModelMetaclass`.
///
/// `ModelMetaclass` defines `__getattr__()` in Python (the private attributes fallback), for which CPython computes
/// -- at class creation, from the names found in the MRO namespaces -- its generic `slot_tp_getattr_hook` slot;
/// this replaces the slot function pointer only, leaving the namespaces untouched, which in CPython terms means:
///
/// - Attribute accesses on classes whose metaclass is exactly `ModelMetaclass` (all models, unless a custom
///   metaclass is involved) go through `model_metaclass_getattro()`: same results, without the generic slot costs.
/// - Nothing changes for metaclasses deriving from `ModelMetaclass` (alone or combined with others, defining
///   `__getattr__()`/`__getattribute__()` or not): CPython computes the slots of a new type from the MRO namespaces
///   (`type_new()` -> `fixup_slot_dispatchers()`, after the pointer inherited by `PyType_Ready()`), where it finds
///   `ModelMetaclass.__getattr__()` (or an override) and hence uses its generic slot, calling `__getattribute__()`
///   and `__getattr__()` as resolved in the MRO exactly as before (`super().__getattr__()` included).
/// - Assigning or deleting `__getattr__`/`__getattribute__` on `ModelMetaclass` (or a base of it) later makes
///   CPython recompute the slot of `ModelMetaclass` and of all its subclasses (`type_setattro()` ->
///   `update_slot()`): the generic slot comes back and the assigned function is honoured.
///
/// So this must only be applied to a heap type deriving from `type` whose own namespace defines `__getattr__()`
/// as a function equivalent to the private attributes fallback and whose `__getattribute__` is `type`'s, which
/// is checked (except for what the function does); it is idempotent. Meant to be called right after the class
/// statement (before the class is used by anything else, a requirement on free-threaded builds).
unsafe extern "C" fn install_model_metaclass_getattro(
    _self: *mut ffi::PyObject,
    metaclass: *mut ffi::PyObject,
) -> *mut ffi::PyObject {
    unsafe {
        let invalid = |detail: &std::ffi::CStr| -> *mut ffi::PyObject {
            ffi::PyErr_Format(
                ffi::PyExc_TypeError,
                c"_install_model_metaclass_getattro() expects a heap type deriving from `type`, defining `__getattr__()` (as a function) but not `__getattribute__()` in its own namespace, and whose `__getattribute__` is `type.__getattribute__`: %s"
                    .as_ptr(),
                detail.as_ptr(),
            );
            std::ptr::null_mut()
        };
        if ffi::PyType_Check(metaclass) == 0 {
            return invalid(c"not a type");
        }
        let tp = metaclass.cast::<ffi::PyTypeObject>();
        let flags = ffi::PyType_GetFlags(tp);
        if flags & ffi::Py_TPFLAGS_TYPE_SUBCLASS == 0 {
            return invalid(c"not a subclass of `type`");
        }
        if flags & ffi::Py_TPFLAGS_HEAPTYPE == 0 {
            return invalid(c"not a heap type");
        }
        let dict = type_own_dict(tp);
        if dict.is_null() {
            return invalid(c"no namespace");
        }
        // Own `__getattr__`, a plain function:
        let mut getattr: *mut ffi::PyObject = std::ptr::null_mut();
        match ffi::compat::PyDict_GetItemRef(dict, GETATTR_STR.load(Ordering::Relaxed), &raw mut getattr) {
            -1 => return std::ptr::null_mut(),
            0 => return invalid(c"no `__getattr__` in its namespace"),
            _ => {
                let is_function = ffi::Py_TYPE(getattr) == std::ptr::addr_of_mut!(ffi::PyFunction_Type);
                ffi::Py_DECREF(getattr);
                if !is_function {
                    return invalid(c"`__getattr__` is not a plain function");
                }
            }
        }
        // No own `__getattribute__`, and the one found in the MRO is `type`'s:
        match ffi::PyDict_Contains(dict, GETATTRIBUTE_STR.load(Ordering::Relaxed)) {
            -1 => return std::ptr::null_mut(),
            0 => {}
            _ => return invalid(c"`__getattribute__` in its namespace"),
        }
        if _PyType_Lookup(tp, GETATTRIBUTE_STR.load(Ordering::Relaxed))
            != TYPE_GETATTRIBUTE_DESCRIPTOR.load(Ordering::Relaxed)
        {
            return invalid(c"`__getattribute__` isn't `type.__getattribute__`");
        }

        let current = getattro_pointer(tp);
        if current != model_metaclass_getattro as *mut c_void {
            if current != TYPE_GETATTRO.load(Ordering::Relaxed) {
                // What CPython computed for a `type` subclass with a Python `__getattr__()`: its generic slot.
                GENERIC_GETATTR_HOOK.store(current, Ordering::Relaxed);
            }
            (*tp).tp_getattro = Some(model_metaclass_getattro);
            ffi::PyType_Modified(tp);
        }
        let none = ffi::Py_None();
        ffi::Py_INCREF(none);
        none
    }
}

/// `_type_own_dict_get(cls, name, default, /)`: `cls.__dict__.get(name, default)`.
unsafe extern "C" fn type_own_dict_get_fastcall(
    _self: *mut ffi::PyObject,
    args: *mut *mut ffi::PyObject,
    nargs: ffi::Py_ssize_t,
) -> *mut ffi::PyObject {
    unsafe {
        if nargs != 3 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_type_own_dict_get() takes exactly 3 positional arguments".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        let (cls, name, default) = (*args, *args.add(1), *args.add(2));
        if ffi::PyType_Check(cls) != 0 && has_standard_type_dict(cls) {
            let dict = type_own_dict(cls.cast::<ffi::PyTypeObject>());
            if !dict.is_null() {
                let mut value: *mut ffi::PyObject = std::ptr::null_mut();
                return match ffi::compat::PyDict_GetItemRef(dict, name, &raw mut value) {
                    -1 => std::ptr::null_mut(),
                    0 => {
                        ffi::Py_INCREF(default);
                        default
                    }
                    _ => value,
                };
            }
        }
        // Anything else: literally `cls.__dict__.get(name, default)`.
        let namespace = ffi::PyObject_GetAttr(cls, DICT_STR.load(Ordering::Relaxed));
        if namespace.is_null() {
            return std::ptr::null_mut();
        }
        let get_args = [namespace, name, default];
        let result = ffi::PyObject_VectorcallMethod(
            GET_STR.load(Ordering::Relaxed),
            get_args.as_ptr(),
            3 | ffi::PY_VECTORCALL_ARGUMENTS_OFFSET,
            std::ptr::null_mut(),
        );
        ffi::Py_DECREF(namespace);
        result
    }
}

/// The interned `'get'` and `'items'` strings (set when the objects are created, live forever).
static GET_STR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());
static ITEMS_STR: AtomicPtr<ffi::PyObject> = AtomicPtr::new(std::ptr::null_mut());

/// `_type_own_namespace_instances(cls, class_or_tuple, skipped_types, /)`:
/// `[(k, v) for k, v in vars(cls).items() if type(v) not in skipped_types and isinstance(v, class_or_tuple)]`
/// (`skipped_types` being a set of types whose instances can't be such instances, as a cheap pre-check).
unsafe extern "C" fn type_own_namespace_instances_fastcall(
    _self: *mut ffi::PyObject,
    args: *mut *mut ffi::PyObject,
    nargs: ffi::Py_ssize_t,
) -> *mut ffi::PyObject {
    unsafe {
        if nargs != 3 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_type_own_namespace_instances() takes exactly 3 positional arguments".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        let (cls, class_or_tuple, skipped_types) = (*args, *args.add(1), *args.add(2));
        if ffi::PyAnySet_Check(skipped_types) == 0 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_type_own_namespace_instances(): skipped_types must be a set".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        // The items to look at, as a list of `(key, value)` tuples (a snapshot: arbitrary code can run below).
        let items = if ffi::PyType_Check(cls) != 0 && has_standard_type_dict(cls) {
            let dict = type_own_dict(cls.cast::<ffi::PyTypeObject>());
            if dict.is_null() {
                ffi::PyList_New(0)
            } else {
                ffi::PyDict_Items(dict)
            }
        } else {
            // Literally `vars(cls).items()`, as a list:
            let namespace = ffi::PyObject_GetAttr(cls, DICT_STR.load(Ordering::Relaxed));
            if namespace.is_null() {
                return std::ptr::null_mut();
            }
            let items_view = ffi::PyObject_VectorcallMethod(
                ITEMS_STR.load(Ordering::Relaxed),
                [namespace].as_ptr(),
                1 | ffi::PY_VECTORCALL_ARGUMENTS_OFFSET,
                std::ptr::null_mut(),
            );
            ffi::Py_DECREF(namespace);
            if items_view.is_null() {
                return std::ptr::null_mut();
            }
            let items = ffi::PySequence_List(items_view);
            ffi::Py_DECREF(items_view);
            items
        };
        if items.is_null() {
            return std::ptr::null_mut();
        }
        let result = ffi::PyList_New(0);
        if result.is_null() {
            ffi::Py_DECREF(items);
            return std::ptr::null_mut();
        }
        let n = ffi::PyList_GET_SIZE(items);
        for i in 0..n {
            let item = ffi::PyList_GET_ITEM(items, i); // borrowed (kept alive by `items`)
            if ffi::PyTuple_Check(item) == 0 || ffi::PyTuple_GET_SIZE(item) != 2 {
                ffi::PyErr_SetString(
                    ffi::PyExc_TypeError,
                    c"_type_own_namespace_instances(): the namespace items must be pairs".as_ptr(),
                );
                ffi::Py_DECREF(result);
                ffi::Py_DECREF(items);
                return std::ptr::null_mut();
            }
            let value = ffi::PyTuple_GET_ITEM(item, 1);
            match ffi::PySet_Contains(skipped_types, ffi::Py_TYPE(value).cast::<ffi::PyObject>()) {
                1 => continue,
                0 => {}
                _ => {
                    // (e.g. an unhashable type: `type(v) not in skipped_types` would raise as well)
                    ffi::Py_DECREF(result);
                    ffi::Py_DECREF(items);
                    return std::ptr::null_mut();
                }
            }
            match ffi::PyObject_IsInstance(value, class_or_tuple) {
                1 => {
                    if ffi::PyList_Append(result, item) != 0 {
                        ffi::Py_DECREF(result);
                        ffi::Py_DECREF(items);
                        return std::ptr::null_mut();
                    }
                }
                0 => {}
                _ => {
                    ffi::Py_DECREF(result);
                    ffi::Py_DECREF(items);
                    return std::ptr::null_mut();
                }
            }
        }
        ffi::Py_DECREF(items);
        result
    }
}

/// `_type_lookup(cls, name, default, /)`: the object `name` is bound to in the namespace of the first class of
/// the MRO of `cls` having it (i.e. what the interpreter looks up -- through the type attribute cache -- before
/// invoking any descriptor), or `default`.
unsafe extern "C" fn type_lookup_fastcall(
    _self: *mut ffi::PyObject,
    args: *mut *mut ffi::PyObject,
    nargs: ffi::Py_ssize_t,
) -> *mut ffi::PyObject {
    unsafe {
        if nargs != 3 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_type_lookup() takes exactly 3 positional arguments".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        let (cls, name, default) = (*args, *args.add(1), *args.add(2));
        if ffi::PyType_Check(cls) == 0 || ffi::PyUnicode_CheckExact(name) == 0 {
            ffi::PyErr_SetString(
                ffi::PyExc_TypeError,
                c"_type_lookup(): expected a class and a string".as_ptr(),
            );
            return std::ptr::null_mut();
        }
        let found = _PyType_Lookup(cls.cast::<ffi::PyTypeObject>(), name);
        let result = if found.is_null() { default } else { found };
        ffi::Py_INCREF(result);
        result
    }
}

struct SyncMethodDef(ffi::PyMethodDef);

// SAFETY: the method definitions are immutable and only point to static data.
unsafe impl Sync for SyncMethodDef {}

static GETATTR_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_model_class_getattr".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunctionFast: model_class_getattr_fastcall,
    },
    ml_flags: ffi::METH_FASTCALL,
    ml_doc: c"_model_class_getattr(cls, name, default, /)\n--\n\n\
Equivalent of `getattr(cls, name, default)` for classes whose metaclass is Pydantic's `ModelMetaclass`, \
cheaper for missing attributes."
        .as_ptr(),
});

static HASATTR_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_model_class_hasattr".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunctionFast: model_class_hasattr_fastcall,
    },
    ml_flags: ffi::METH_FASTCALL,
    ml_doc: c"_model_class_hasattr(cls, name, /)\n--\n\n\
Equivalent of `hasattr(cls, name)` for classes whose metaclass is Pydantic's `ModelMetaclass`, \
cheaper for missing attributes."
        .as_ptr(),
});

static OWN_DICT_GET_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_type_own_dict_get".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunctionFast: type_own_dict_get_fastcall,
    },
    ml_flags: ffi::METH_FASTCALL,
    ml_doc: c"_type_own_dict_get(cls, name, default, /)\n--\n\n\
Equivalent of `cls.__dict__.get(name, default)`, cheaper for classes with the standard `__dict__` attribute."
        .as_ptr(),
});

static OWN_NAMESPACE_INSTANCES_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_type_own_namespace_instances".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunctionFast: type_own_namespace_instances_fastcall,
    },
    ml_flags: ffi::METH_FASTCALL,
    ml_doc: c"_type_own_namespace_instances(cls, class_or_tuple, skipped_types, /)\n--\n\n\
Equivalent of `[(k, v) for k, v in vars(cls).items() if type(v) not in skipped_types and isinstance(v, class_or_tuple)]`."
        .as_ptr(),
});

static TYPE_LOOKUP_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_type_lookup".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunctionFast: type_lookup_fastcall,
    },
    ml_flags: ffi::METH_FASTCALL,
    ml_doc: c"_type_lookup(cls, name, default, /)\n--\n\n\
The object `name` is bound to in the namespace of the first class of the MRO of `cls` having it, or `default`."
        .as_ptr(),
});

static INSTALL_MODEL_METACLASS_GETATTRO_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_install_model_metaclass_getattro".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunction: install_model_metaclass_getattro,
    },
    ml_flags: ffi::METH_O,
    ml_doc: c"_install_model_metaclass_getattro(metaclass, /)\n--\n\n\
Implement the class attributes access of Pydantic's `ModelMetaclass` (`type.__getattribute__()`, and for missing \
attributes the private attributes fallback of its `__getattr__()`) as the C-level slot of that exact type object."
        .as_ptr(),
});

/// Fetch (once) the descriptor bound to a name in the namespace of `type` (a borrowed reference to an object of a
/// static type's namespace, kept forever).
unsafe fn type_descriptor_once(target: &AtomicPtr<ffi::PyObject>, name: &AtomicPtr<ffi::PyObject>) -> PyResult<()> {
    unsafe {
        if target.load(Ordering::Relaxed).is_null() {
            let descriptor = _PyType_Lookup(std::ptr::addr_of_mut!(ffi::PyType_Type), name.load(Ordering::Relaxed));
            if descriptor.is_null() {
                return Err(pyo3::exceptions::PyRuntimeError::new_err(
                    "a descriptor of `type` can't be found",
                ));
            }
            ffi::Py_INCREF(descriptor);
            target.store(descriptor, Ordering::Relaxed);
        }
        Ok(())
    }
}

fn make_function<'py>(module: &Bound<'py, PyModule>, def: &'static SyncMethodDef) -> PyResult<Bound<'py, PyAny>> {
    let py = module.py();
    let module_name = module.name()?;
    // SAFETY: the definition is a valid method definition living forever, `PyCMethod_New`
    // returns a new reference or null with an exception set.
    unsafe {
        Bound::from_owned_ptr_or_err(
            py,
            ffi::PyCMethod_New(
                std::ptr::addr_of!(def.0).cast_mut(),
                std::ptr::null_mut(),
                module_name.as_ptr(),
                std::ptr::null_mut(),
            ),
        )
    }
}

/// The objects to be added to the module: the `_model_class_getattr`, `_model_class_hasattr`,
/// `_type_own_dict_get`, `_type_own_namespace_instances`, `_type_lookup` and `_install_model_metaclass_getattro`
/// built-in functions.
pub struct ModelClassLookupObjects<'py> {
    pub model_class_getattr: Bound<'py, PyAny>,
    pub model_class_hasattr: Bound<'py, PyAny>,
    pub type_own_dict_get: Bound<'py, PyAny>,
    pub type_own_namespace_instances: Bound<'py, PyAny>,
    pub type_lookup: Bound<'py, PyAny>,
    pub install_model_metaclass_getattro: Bound<'py, PyAny>,
}

/// Intern (and leak) a string, once.
unsafe fn intern_once(target: &AtomicPtr<ffi::PyObject>, value: &std::ffi::CStr, py: Python<'_>) -> PyResult<()> {
    unsafe {
        if target.load(Ordering::Relaxed).is_null() {
            let s = ffi::PyUnicode_InternFromString(value.as_ptr());
            if s.is_null() {
                return Err(PyErr::fetch(py));
            }
            target.store(s, Ordering::Relaxed);
        }
        Ok(())
    }
}

/// Create the objects to be added to the module, see `ModelClassLookupObjects`.
pub fn make_model_class_lookup_objects<'py>(module: &Bound<'py, PyModule>) -> PyResult<ModelClassLookupObjects<'py>> {
    let py = module.py();
    // SAFETY: creating (and leaking) interned strings; fetching a descriptor living forever from a static type.
    unsafe {
        intern_once(&PRIVATE_ATTRIBUTES_STR, c"__private_attributes__", py)?;
        intern_once(&DICT_STR, c"__dict__", py)?;
        intern_once(&GETATTR_STR, c"__getattr__", py)?;
        intern_once(&GETATTRIBUTE_STR, c"__getattribute__", py)?;
        intern_once(&GET_STR, c"get", py)?;
        intern_once(&ITEMS_STR, c"items", py)?;
        type_descriptor_once(&TYPE_DICT_DESCRIPTOR, &DICT_STR)?;
        type_descriptor_once(&TYPE_GETATTRIBUTE_DESCRIPTOR, &GETATTRIBUTE_STR)?;
        // SAFETY: reading a type slot of a valid static type object.
        TYPE_GETATTRO.store(
            getattro_pointer(std::ptr::addr_of_mut!(ffi::PyType_Type)),
            Ordering::Relaxed,
        );
    }
    Ok(ModelClassLookupObjects {
        model_class_getattr: make_function(module, &GETATTR_DEF)?,
        model_class_hasattr: make_function(module, &HASATTR_DEF)?,
        type_own_dict_get: make_function(module, &OWN_DICT_GET_DEF)?,
        type_own_namespace_instances: make_function(module, &OWN_NAMESPACE_INSTANCES_DEF)?,
        type_lookup: make_function(module, &TYPE_LOOKUP_DEF)?,
        install_model_metaclass_getattro: make_function(module, &INSTALL_MODEL_METACLASS_GETATTRO_DEF)?,
    })
}
