import pydantic
from benchmarks import test_pydantic
from benchmarks.get_profiler import get_line_profiler
from benchmarks.run import run_tests


def get_funcs_to_profile():
    """
    I produced this cascading list of functions by starting with run_pydantic_tests,
    and adding the most expensive call from the line-by-line output until I had to start adding
    them to the profiler in-line (e.g., when the most expensive call is a lambda).

    You can comment/uncomment each line to include/exclude the line-by-line profiling for that function.
    """
    funcs_to_profile = []
    funcs_to_profile += [run_tests]
    funcs_to_profile += [test_pydantic.TestPydantic.validate]
    funcs_to_profile += [test_pydantic.Model.__init__]
    funcs_to_profile += [pydantic.validate_model]
    funcs_to_profile += [pydantic.fields.Field.validate]
    funcs_to_profile += [pydantic.fields.Field._validate_singleton]
    funcs_to_profile += [pydantic.fields.Field._apply_validators]

    # The next most expensive line was pydantic.fields._apply_validators line 432;
    # extracting the relevant functions was easier to do in-line -- see line 430 of that file
    #
    # The next most expensive lines after that were lambdas; see class_validators.py line 198.
    #
    # The next most expensive lines were actual validators. That is where I stopped digging.
    return funcs_to_profile


def profile(
        funcs_to_profile,
        main_func,
        *main_func_args,
        **main_func_kwargs
):
    profiler = get_line_profiler()
    for f in funcs_to_profile:
        profiler.add_function(f)
    wrapped = profiler.wrap_function(main_func)
    wrapped(*main_func_args, **main_func_kwargs)
    get_line_profiler().print_stats()


def main():
    profile(
        funcs_to_profile=get_funcs_to_profile(),
        main_func=run_tests,
        tests=[test_pydantic.TestPydantic]
    )


if __name__ == '__main__':
    main()
