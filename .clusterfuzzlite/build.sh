cp $SRC/parse.py $SRC/pydantic/
# Build and install project (using current CFLAGS, CXXFLAGS).
pip3 install --upgrade pip
pip3 install .

compile_python_fuzzer pydantic/fuzz_parse.py
