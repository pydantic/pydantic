use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use ahash::{AHashMap, AHashSet};

use crate::build_tools::{py_err, py_error_type, SchemaDict};
use crate::questions::Answers;
use crate::serializers::CombinedSerializer;
use crate::validators::{CombinedValidator, Validator};

#[derive(Clone, Debug)]
struct Slot<T> {
    slot_ref: String,
    op_val_ser: Option<T>,
    answers: Option<Answers>,
}

pub enum ThingOrId<T> {
    Thing(T),
    Id(usize),
}

/// `BuildContext` is used to store extra information while building validators and type_serializers
#[derive(Clone, Debug)]
pub struct BuildContext<T> {
    /// set of used refs, useful to see if a `ref` is actually used elsewhere in the schema
    used_refs: AHashSet<String>,
    /// holds validators/type_serializers which reference themselves and therefore can't be cloned and owned
    /// in one or multiple places.
    slots: Vec<Slot<T>>,
    /// holds validators/type_serializers which need to be accessed from multiple other validators/type_serializers
    /// and therefore can't be owned by them directly.
    reusable: AHashMap<String, T>,
}

impl<T: Clone + std::fmt::Debug> BuildContext<T> {
    pub fn new(schema: &PyAny) -> PyResult<Self> {
        let mut used_refs = AHashSet::new();
        extract_used_refs(schema, &mut used_refs)?;
        Ok(Self {
            used_refs,
            slots: Vec::new(),
            reusable: AHashMap::new(),
        })
    }

    pub fn for_self_schema() -> Self {
        let mut used_refs = AHashSet::with_capacity(3);
        // NOTE: we don't call `extract_used_refs` for performance reasons, if more recursive references
        // are used, they would need to be manually added here.
        // we use `2` as count to avoid `find_slot` pulling the validator out of slots and returning it directly
        used_refs.insert("root-schema".to_string());
        used_refs.insert("ser-schema".to_string());
        used_refs.insert("inc-ex-type".to_string());
        Self {
            used_refs,
            slots: Vec::new(),
            reusable: AHashMap::new(),
        }
    }

    /// Check whether a ref is already in `reusable` or `slots`, we shouldn't allow repeated refs
    pub fn ref_already_used(&self, ref_: &str) -> bool {
        self.reusable.contains_key(ref_) || self.slots.iter().any(|slot| slot.slot_ref == ref_)
    }

    /// check if a ref is used elsewhere in the schema
    pub fn ref_used(&self, ref_: &str) -> bool {
        self.used_refs.contains(ref_)
    }

    /// check if a ref is used within a given schema
    pub fn ref_used_within(&self, schema_dict: &PyAny, ref_: &str) -> PyResult<bool> {
        check_ref_used(schema_dict, ref_)
    }

    /// add a validator/serializer to `reusable` so it can be cloned and used again elsewhere
    pub fn store_reusable(&mut self, ref_: String, val_ser: T) {
        self.reusable.insert(ref_, val_ser);
    }

    /// First of two part process to add a new validator/serializer slot, we add the `slot_ref` to the array,
    /// but not the actual `validator`/`serializer`, we can't add that until it's build.
    /// But we need the `id` to build it, hence this two-step process.
    pub fn prepare_slot(&mut self, slot_ref: String, answers: Option<Answers>) -> PyResult<usize> {
        let id = self.slots.len();
        let slot = Slot {
            slot_ref,
            op_val_ser: None,
            answers,
        };
        self.slots.push(slot);
        Ok(id)
    }

    /// Second part of adding a validator/serializer - we update the slot to include a validator
    pub fn complete_slot(&mut self, slot_id: usize, val_ser: T) -> PyResult<()> {
        match self.slots.get(slot_id) {
            Some(slot) => {
                self.slots[slot_id] = Slot {
                    slot_ref: slot.slot_ref.clone(),
                    op_val_ser: Some(val_ser),
                    answers: slot.answers.clone(),
                };
                Ok(())
            }
            None => py_err!("Slots Error: slot {} not found", slot_id),
        }
    }

    /// find validator/serializer by `ref`, if the `ref` is in `resuable` return a clone of the validator/serializer,
    /// otherwise return the id of the slot.
    pub fn find(&mut self, ref_: &str) -> PyResult<ThingOrId<T>> {
        if let Some(val_ser) = self.reusable.get(ref_) {
            Ok(ThingOrId::Thing(val_ser.clone()))
        } else {
            let id = match self.slots.iter().position(|slot| slot.slot_ref == ref_) {
                Some(id) => id,
                None => return py_err!("Slots Error: ref '{}' not found", ref_),
            };
            Ok(ThingOrId::Id(id))
        }
    }

    /// get a slot answer by `id`
    pub fn get_slot_answer(&self, slot_id: usize) -> PyResult<Option<Answers>> {
        match self.slots.get(slot_id) {
            Some(slot) => Ok(slot.answers.clone()),
            None => py_err!("Slots Error: slot {} not found", slot_id),
        }
    }

    /// find a validator/serializer by `slot_id` - this used in `Validator.complete`,
    /// specifically `RecursiveRefValidator` to set its name
    pub fn find_validator(&self, slot_id: usize) -> PyResult<&T> {
        match self.slots.get(slot_id) {
            Some(slot) => match slot.op_val_ser {
                Some(ref validator) => Ok(validator),
                None => py_err!("Slots Error: slot {} not yet filled", slot_id),
            },
            None => py_err!("Slots Error: slot {} not found", slot_id),
        }
    }
}

impl BuildContext<CombinedValidator> {
    /// Move validators into a new vec which maintains the order of slots, `complete` is called on each validator
    /// at the same time.
    pub fn into_slots_val(self) -> PyResult<Vec<CombinedValidator>> {
        let self_clone = self.clone();
        self.slots
            .into_iter()
            .map(|slot| match slot.op_val_ser {
                Some(mut validator) => {
                    validator.complete(&self_clone)?;
                    Ok(validator)
                }
                None => py_err!("Slots Error: slot not yet filled"),
            })
            .collect()
    }
}

impl BuildContext<CombinedSerializer> {
    /// Move validators into a new vec which maintains the order of slots
    pub fn into_slots_ser(self) -> PyResult<Vec<CombinedSerializer>> {
        self.slots
            .into_iter()
            .map(|slot| {
                slot.op_val_ser
                    .ok_or_else(|| py_error_type!("Slots Error: slot not yet filled"))
            })
            .collect()
    }
}

fn extract_used_refs(schema: &PyAny, refs: &mut AHashSet<String>) -> PyResult<()> {
    if let Ok(dict) = schema.downcast::<PyDict>() {
        if is_definition_ref(dict)? {
            refs.insert(dict.get_as_req(intern!(schema.py(), "schema_ref"))?);
        } else {
            for (_, value) in dict.iter() {
                extract_used_refs(value, refs)?;
            }
        }
    } else if let Ok(list) = schema.downcast::<PyList>() {
        for item in list.iter() {
            extract_used_refs(item, refs)?;
        }
    }
    Ok(())
}

fn check_ref_used(schema: &PyAny, ref_: &str) -> PyResult<bool> {
    if let Ok(dict) = schema.downcast::<PyDict>() {
        if is_definition_ref(dict)? {
            let key: &str = dict.get_as_req(intern!(schema.py(), "schema_ref"))?;
            return Ok(key == ref_);
        } else {
            for (_, value) in dict.iter() {
                if check_ref_used(value, ref_)? {
                    return Ok(true);
                }
            }
        }
    } else if let Ok(list) = schema.downcast::<PyList>() {
        for item in list.iter() {
            if check_ref_used(item, ref_)? {
                return Ok(true);
            }
        }
    }
    Ok(false)
}

fn is_definition_ref(dict: &PyDict) -> PyResult<bool> {
    match dict.get_item(intern!(dict.py(), "type")) {
        Some(type_value) => type_value.eq(intern!(dict.py(), "definition-ref")),
        None => Ok(false),
    }
}
