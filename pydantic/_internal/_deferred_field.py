from pydantic._internal._generics import replace_types


class DeferredField:
    def __init__(self, bases, ann_name):
        self.bases = bases
        self.ann_name = ann_name
        self.substitutions = []

    def replace_types(self, typevars_map):
        self.substitutions.append(typevars_map)
