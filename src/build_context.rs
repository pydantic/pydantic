use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use ahash::AHashSet;

use crate::build_tools::{py_err, py_error_type, SchemaDict};
use crate::questions::Answers;
use crate::serializers::CombinedSerializer;
use crate::validators::{CombinedValidator, Validator};

#[derive(Clone)]
struct Slot<T> {
    slot_ref: String,
    op_val_ser: Option<T>,
    answers: Option<Answers>,
}

/// `BuildContext` is used to store extra information while building validators and type_serializers,
/// currently it just holds a vec "slots" which holds validators/type_serializers which need to be accessed from
/// multiple other validators/type_serializers and therefore can't be owned by them directly.
#[derive(Clone)]
pub struct BuildContext<T> {
    used_refs: AHashSet<String>,
    slots: Vec<Slot<T>>,
}

impl<T: Clone> BuildContext<T> {
    pub fn new(used_refs: AHashSet<String>) -> Self {
        Self {
            used_refs,
            slots: Vec::new(),
        }
    }

    pub fn for_schema(schema: &PyAny) -> PyResult<Self> {
        let mut used_refs = AHashSet::new();
        extract_used_refs(schema, &mut used_refs)?;
        Ok(Self {
            used_refs,
            slots: Vec::new(),
        })
    }

    pub fn for_self_schema() -> Self {
        let mut used_refs = AHashSet::new();
        // NOTE: we don't call `extract_used_refs` for performance reasons, if more recursive references
        // are used, they would need to be manually added here.
        used_refs.insert("root-schema".to_string());
        used_refs.insert("ser-schema".to_string());
        used_refs.insert("inc-ex-type".to_string());
        Self {
            used_refs,
            slots: Vec::new(),
        }
    }

    /// check if a ref is used elsewhere in the schema
    pub fn ref_used(&self, ref_: &str) -> bool {
        self.used_refs.contains(ref_)
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

    /// find a slot by `slot_ref` - iterate over the slots until we find a matching reference - return the index
    pub fn find_slot_id_answer(&self, slot_ref: &str) -> PyResult<(usize, Option<Answers>)> {
        let is_match = |slot: &Slot<T>| slot.slot_ref == slot_ref;
        match self.slots.iter().position(is_match) {
            Some(id) => {
                let slot = self.slots.get(id).unwrap();
                Ok((id, slot.answers.clone()))
            }
            None => py_err!("Slots Error: ref '{}' not found", slot_ref),
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
    if let Ok(dict) = schema.cast_as::<PyDict>() {
        let py = schema.py();
        if matches!(dict.get_as(intern!(py, "type")), Ok(Some("recursive-ref"))) {
            refs.insert(dict.get_as_req(intern!(py, "schema_ref"))?);
        } else {
            for (_, value) in dict.iter() {
                extract_used_refs(value, refs)?;
            }
        }
    } else if let Ok(list) = schema.cast_as::<PyList>() {
        for item in list.iter() {
            extract_used_refs(item, refs)?;
        }
    }
    Ok(())
}
