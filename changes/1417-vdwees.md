Modify schema constraints on ConstrainedFloat so that exclusiveMinimum and
minimum are not included in the schema if they are equal to `-math.inf` and
exclusiveMaximum and maximum are not included if they are equal to `math.inf.
