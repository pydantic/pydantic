use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use ahash::AHashSet;

use crate::build_tools::{py_error, SchemaDict};
use crate::questions::Answers;
use crate::validators::{CombinedValidator, Validator};

#[derive(Clone)]
struct Slot {
    slot_ref: String,
    op_validator: Option<CombinedValidator>,
    answers: Answers,
}

/// `BuildContext` is used to store extra information while building validators,
/// currently it just holds a vec "slots" which holds validators need to be accessed from multiple other validators
/// and therefore can't be owned by them directly.
#[derive(Default, Clone)]
pub struct BuildContext {
    used_refs: AHashSet<String>,
    slots: Vec<Slot>,
}

impl BuildContext {
    pub fn new(used_refs: AHashSet<String>) -> Self {
        Self {
            used_refs,
            ..Default::default()
        }
    }

    /// check if a ref is used elsewhere in the schema
    pub fn ref_used(&self, ref_: &str) -> bool {
        self.used_refs.contains(ref_)
    }

    /// First of two part process to add a new validator slot, we add the `slot_ref` to the array, but not the
    /// actual `validator`, we can't add the validator until it's build.
    /// We need the `id` to build the validator, hence this two-step process.
    pub fn prepare_slot(&mut self, slot_ref: String, answers: Answers) -> PyResult<usize> {
        let id = self.slots.len();
        let slot = Slot {
            slot_ref,
            op_validator: None,
            answers,
        };
        self.slots.push(slot);
        Ok(id)
    }

    /// Second part of adding a validator - we update the slot to include a validator
    pub fn complete_slot(&mut self, slot_id: usize, validator: CombinedValidator) -> PyResult<()> {
        match self.slots.get(slot_id) {
            Some(slot) => {
                self.slots[slot_id] = Slot {
                    slot_ref: slot.slot_ref.clone(),
                    op_validator: Some(validator),
                    answers: slot.answers.clone(),
                };
                Ok(())
            }
            None => py_error!("Slots Error: slot {} not found", slot_id),
        }
    }

    /// find a slot by `slot_ref` - iterate over the slots until we find a matching reference - return the index
    pub fn find_slot_id_answer(&self, slot_ref: &str) -> PyResult<(usize, Answers)> {
        let is_match = |slot: &Slot| slot.slot_ref == slot_ref;
        match self.slots.iter().position(is_match) {
            Some(id) => {
                let slot = self.slots.get(id).unwrap();
                Ok((id, slot.answers.clone()))
            }
            None => py_error!("Slots Error: ref '{}' not found", slot_ref),
        }
    }

    /// find a validator by `slot_id` - this used in `Validator.complete`, specifically `RecursiveRefValidator`
    /// to set its name
    pub fn find_validator(&self, slot_id: usize) -> PyResult<&CombinedValidator> {
        match self.slots.get(slot_id) {
            Some(slot) => match slot.op_validator {
                Some(ref validator) => Ok(validator),
                None => py_error!("Slots Error: slot {} not yet filled", slot_id),
            },
            None => py_error!("Slots Error: slot {} not found", slot_id),
        }
    }

    /// Move validators into a new vec which maintains the order of slots, `complete` is called on each validator
    /// at the same time.
    pub fn into_slots(self) -> PyResult<Vec<CombinedValidator>> {
        let self_clone = self.clone();
        self.slots
            .into_iter()
            .map(|slot| match slot.op_validator {
                Some(mut validator) => {
                    validator.complete(&self_clone)?;
                    Ok(validator)
                }
                None => py_error!("Slots Error: slot not yet filled"),
            })
            .collect()
    }
}

pub fn extract_used_refs(schema: &PyAny, refs: &mut AHashSet<String>) -> PyResult<()> {
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
