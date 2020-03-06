Raise more informative ``TypeError`` in ``pydantic.utils.ValueItems.__init__``
when ``value`` is a list/tuple and the exclusion kwarg is improperly indexed.
Added special handling for the exclusion key ``'__all__'``, which allows one to
exclude fields from all elements of a list/tuple of submodels. Added example to
Exporting Models docs.
