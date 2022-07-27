cp $SRC/parse.py $SRC/pydantic/
# Build and install project (using current CFLAGS, CXXFLAGS).
pip3 install --upgrade pip
pip3 install .

cp pydantic/fuzz_parse.py $SRC/
compile_python_fuzzer $SRC/fuzz_parse.py
