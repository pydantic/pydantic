cp $SRC/parse.py $SRC/pydantic/
# Build and install project (using current CFLAGS, CXXFLAGS).
pip3 install --upgrade pip
pip3 install .
for fuzzer in $(find $SRC -name 'fuzz_*.py'); do
  compile_python_fuzzer $fuzzer
done
