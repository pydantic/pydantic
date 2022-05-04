use super::parse_json::{JsonArray, JsonObject};
use super::{Input, ToPy};
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyTuple};

// these are ugly, is there any way to avoid the maps in iter, one of the boxes and/or the duplication?
// is this harming performance, particularly the .map(|item| item)?
// https://stackoverflow.com/a/47156134/949890
pub trait ListInput<'data>: ToPy {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data>;

    fn input_len(&self) -> usize;
}

impl<'data> ListInput<'data> for &'data PyList {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'data> ListInput<'data> for &'data PyTuple {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'data> ListInput<'data> for &'data PySet {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'data> ListInput<'data> for &'data PyFrozenSet {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'data> ListInput<'data> for &'data JsonArray {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

///////////////////////

pub trait DictInput<'data>: ToPy {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&'data dyn Input, &'data dyn Input)> + 'data>;

    fn input_get(&self, key: &str) -> Option<&'data dyn Input>;

    fn input_len(&self) -> usize;
}

impl<'data> DictInput<'data> for &'data PyDict {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&'data dyn Input, &'data dyn Input)> + 'data> {
        Box::new(self.iter().map(|(k, v)| (k as &dyn Input, v as &dyn Input)))
    }

    fn input_get(&self, key: &str) -> Option<&'data dyn Input> {
        self.get_item(key).map(|item| item as &dyn Input)
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'data> DictInput<'data> for &'data JsonObject {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&'data dyn Input, &'data dyn Input)> + 'data> {
        Box::new(self.iter().map(|(k, v)| (k as &dyn Input, v as &dyn Input)))
    }

    fn input_get(&self, key: &str) -> Option<&'data dyn Input> {
        self.get(key).map(|item| item as &dyn Input)
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}
