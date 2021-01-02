**Breaking Change:** always validate only first sublevel items with `each_item`.
There were indeed some edge cases with some compound types where the validated items were the last sublevel ones.