``pydantic.main.ModelMetaclass.__new__`` should include ``**kwargs`` at the
end of the method definition and pass them on to the ``super`` call at
the end in order to allow the special method ```__init_subclass__```_ to
be defined with custom parameters on extended ``BaseModel`` classes.
