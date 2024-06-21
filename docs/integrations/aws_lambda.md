`pydantic` integrates well with AWS Lambda functions. In this guide, we'll discuss how to setup `pydantic` for an AWS Lambda function.

## Installing Python libraries for AWS Lambda functions

There are many ways to utilize Python libraries in AWS Lambda functions. As outlined in the [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html), the most common approaches include:

* Using a [`.zip` file archive](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html) to package your code and dependencies
* Using [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html) to share libraries across multiple functions
* Using a [container image](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) to package your code and dependencies

All of these approaches can be used with `pydantic`. The best approach for you will depend on your specific requirements and constraints. We'll cover the first two cases more in-depth here, as dependency management with
a container image is more straightforward. If you're using a container image, you might find [this comment](https://github.com/pydantic/pydantic/issues/6557#issuecomment-1699456562) helpful for installing `pydantic`.

!!! tip
    If you use `pydantic` across multiple functions, you may want to consider AWS Lambda Layers, which support seamless sharing of libraries across multiple functions.

Regardless of the dependencies management approach you choose, it's beneficial to adhere to these guidelines to ensure a smooth
dependency management process.

## Installing `pydantic` for AWS Lambda functions

When you're building your `.zip` file archive with your code and dependencies or organizing your `.zip` file for a Lambda Layer, you'll likely use a local virtual environment to install and manage your dependencies. This can be a bit tricky if you're using `pip` because `pip` installs wheels compiled for your local platform, which may not be compatible with the Lambda environment.

Thus, we suggest you use a command similar to the following:

```bash
pip install \
    --platform manylinux2014_x86_64 \  # (1)!
    --target=<your_package_dir> \  # (2)!
    --implementation cp \  # (3)!
    --python-version 3.10 \  # (4)!
    --only-binary=:all: \  # (5)!
    --upgrade pydantic  # (6)!
```

1. Use the platform corresponding to your Lambda runtime.
2. Specify the directory where you want to install the package (often `python` for Lambda Layers).
3. Use the CPython implementation.
4. The Python version must be compatible with the Lambda runtime.
5. This flag ensures that the package is installed pre-built binary wheels.
6. The latest version of `pydantic` will be installed.

## Troubleshooting

!!! warning "How to fix the `no module named 'pydantic_core._pydantic_core'` error"
    The
    ```
    no module named `pydantic_core._pydantic_core`
    ```

    error is a common issue that indicates you have installed `pydantic` incorrectly. To debug this issue, you can try the following steps (before the failing import):

    1. Check the contents of the installed `pydantic-core` package. Are the compiled library and its type stubs both present?

    ```py test="skip" lint="skip"
    from importlib.metadata import files
    print([file for file in files('pydantic-core') if file.name.startswith('_pydantic_core')])
    """
    [PackagePath('pydantic_core/_pydantic_core.pyi'), PackagePath('pydantic_core/_pydantic_core.cpython-312-x86_64-linux-gnu.so')]
    """
    ```

    You should expect to see two files like those printed above. The compile library file will be a .so or .pyd with a name that varies according to the OS and Python version.

    2. Check that your lambda's Python version is compatible with the compiled library version found above.

    ```py test="skip" lint="skip"
    import sysconfig
    print(sysconfig.get_config_var("EXT_SUFFIX"))
    #> '.cpython-312-x86_64-linux-gnu.so'
    ```

    You should expect to see the same suffix here as the compiled library, for example here we see this suffix `.cpython-312-x86_64-linux-gnu.so` indeed matches `_pydantic_core.cpython-312-x86_64-linux-gnu.so`.

    If these two checks do not match, your build steps have not installed the correct native code for your lambda's target platform. You should adjust your build steps to change the version of the installed library which gets installed.

    Most likely errors:

    * Your OS or CPU architecture is mismatched (e.g. darwin vs x86_64-linux-gnu). Try passing correct `--platform` argument to `pip install` when installing your lambda dependencies, or build inside a linux docker container for the correct platform. Possible platforms at the moment include `--platform manylinux2014_x86_64` or `--platform manylinux2014_aarch64`, but these may change with a future Pydantic major release.

    * Your Python version is mismatched (e.g. `cpython-310` vs `cpython-312`). Try passing correct `--python-version` argument to `pip install`, or otherwise change the Python version used on your build.


## Extra Resources

### More Debugging Tips

If you're still struggling with installing `pydantic` for your AWS Lambda, you might consult with [this issue](https://github.com/pydantic/pydantic/issues/6557), which covers a variety of problems and solutions encountered by other developers.


### Validating `event` and `context` data

Check out our [blog post](https://pydantic.dev/articles/lambda-intro) to learn more about how to use `pydantic` to validate `event` and `context` data in AWS Lambda functions.
