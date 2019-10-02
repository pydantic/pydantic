Below are the results of crude benchmarks comparing *pydantic* to other validation libraries.

**TODO**

See [the benchmarks code](https://github.com/samuelcolvin/pydantic/tree/master/benchmarks)
for more details on the test case. Feel free to suggest more packages to benchmark or improve an existing one.

Benchmarks were run with python 3.7.2 and the following package versions:

* **pydantic** pre `v0.27`
  [d473f4a](https://github.com/samuelcolvin/pydantic/commit/d473f4abc9d040c8c90e102017aacfc078f0f37d) compiled with
  cython
* **toasted-marshmallow** `v0.2.6`
* **marshmallow** the version installed by `toasted-marshmallow`, see
  [this](https://github.com/lyft/toasted-marshmallow/issues/9) issue.
* **trafaret** `v1.2.0`
* **django-restful-framework** `v3.9.4`
