echo "Recreating requirements/*.txt files using pip-compile"

# delete the lockfiles
find requirements -name "*.txt" -type f -delete
# rebuild them
./requirements/refresh.sh
