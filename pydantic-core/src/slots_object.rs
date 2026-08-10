//! `_copy_slots_object(obj, /)`: a shallow copy of an instance of a class only made of `__slots__` (as `FieldInfo`
//! is), i.e. a new instance -- allocated like `object.__new__(type(obj))`, `__init__()` not called -- with every
//! member set to the same object as in `obj`, in one call instead of a `copied.x = self.x` statement per member.
//!
//! This is a raw `METH_O` function; a pure Python version is used on other Python implementations.
use std::ffi::c_void;

use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::types::PyModule;

/// Whether `tp` (any type) is a heap type.
#[inline]
unsafe fn is_heap_type(tp: *mut ffi::PyTypeObject) -> bool {
    unsafe { ((*tp).tp_flags & ffi::Py_TPFLAGS_HEAPTYPE) != 0 }
}

unsafe extern "C" fn copy_slots_object(_self: *mut ffi::PyObject, obj: *mut ffi::PyObject) -> *mut ffi::PyObject {
    unsafe {
        let tp = ffi::Py_TYPE(obj);
        // Only for instances of heap types without an instance dictionary (i.e. classes and bases all defining
        // `__slots__`), whose allocation is the generic one (that of `object`, i.e. `PyType_GenericAlloc`):
        // (both are slot values read from type objects, compared as data)
        let alloc = (*tp)
            .tp_alloc
            .map_or(std::ptr::null::<c_void>(), |f| f as *const c_void);
        let generic_alloc = (*std::ptr::addr_of!(ffi::PyBaseObject_Type))
            .tp_alloc
            .map_or(std::ptr::null::<c_void>(), |f| f as *const c_void);
        if !is_heap_type(tp) || (*tp).tp_dictoffset != 0 || alloc != generic_alloc {
            ffi::PyErr_Format(
                ffi::PyExc_TypeError,
                c"_copy_slots_object(): expected an instance of a class only made of __slots__, got a '%.100s'"
                    .as_ptr(),
                (*tp).tp_name,
            );
            return std::ptr::null_mut();
        }
        // What `object.__new__(cls)` comes down to for such a (non abstract) class:
        let copied = ffi::PyType_GenericAlloc(tp, 0);
        if copied.is_null() {
            return std::ptr::null_mut();
        }
        // The members of every (heap) class of the MRO, i.e. the `__slots__` of each of them:
        let mro = (*tp).tp_mro;
        let n = ffi::PyTuple_GET_SIZE(mro);
        for i in 0..n {
            let base = ffi::PyTuple_GET_ITEM(mro, i).cast::<ffi::PyTypeObject>();
            if !is_heap_type(base) {
                continue;
            }
            let mut member = (*base).tp_members;
            if member.is_null() {
                continue;
            }
            while !(*member).name.is_null() {
                if (*member).type_code == ffi::Py_T_OBJECT_EX {
                    let offset = (*member).offset;
                    // (member offsets are pointer-aligned by construction)
                    #[allow(clippy::cast_ptr_alignment)]
                    let src = obj.cast::<u8>().offset(offset).cast::<*mut ffi::PyObject>();
                    let value = *src;
                    if value.is_null() {
                        // (what reading the attribute raises)
                        ffi::PyErr_Format(
                            ffi::PyExc_AttributeError,
                            c"'%.100s' object has no attribute '%s'".as_ptr(),
                            (*tp).tp_name,
                            (*member).name,
                        );
                        ffi::Py_DECREF(copied);
                        return std::ptr::null_mut();
                    }
                    #[allow(clippy::cast_ptr_alignment)]
                    let dst = copied.cast::<u8>().offset(offset).cast::<*mut ffi::PyObject>();
                    let previous = *dst;
                    ffi::Py_INCREF(value);
                    *dst = value;
                    if !previous.is_null() {
                        // (the same slot listed by two classes of the MRO)
                        ffi::Py_DECREF(previous);
                    }
                }
                member = member.add(1);
            }
        }
        copied
    }
}

struct SyncMethodDef(ffi::PyMethodDef);

// SAFETY: the method definition is immutable and only points to static data.
unsafe impl Sync for SyncMethodDef {}

static COPY_SLOTS_OBJECT_DEF: SyncMethodDef = SyncMethodDef(ffi::PyMethodDef {
    ml_name: c"_copy_slots_object".as_ptr(),
    ml_meth: ffi::PyMethodDefPointer {
        PyCFunction: copy_slots_object,
    },
    ml_flags: ffi::METH_O,
    ml_doc: c"_copy_slots_object(obj, /)\n--\n\n\
A shallow copy of an instance of a class only made of `__slots__`: a new instance (`__init__()` not called) \
with every member set to the same object (an `AttributeError` is raised for an unset one)."
        .as_ptr(),
});

/// Create the `_copy_slots_object` built-in function object, to be added to the module.
pub fn make_copy_slots_object<'py>(module: &Bound<'py, PyModule>) -> PyResult<Bound<'py, PyAny>> {
    let py = module.py();
    let module_name = module.name()?;
    // SAFETY: the definition is a valid method definition living forever, `PyCMethod_New`
    // returns a new reference or null with an exception set.
    unsafe {
        Bound::from_owned_ptr_or_err(
            py,
            ffi::PyCMethod_New(
                std::ptr::addr_of!(COPY_SLOTS_OBJECT_DEF.0).cast_mut(),
                std::ptr::null_mut(),
                module_name.as_ptr(),
                std::ptr::null_mut(),
            ),
        )
    }
}
