Added additional check to the validator function that throws a descriptive
ConfigError if the values of the 'fields' parameter is incorrectly set.
Added test to ensure ConfigError is raised when validator decorator fields
are incorrectly set.