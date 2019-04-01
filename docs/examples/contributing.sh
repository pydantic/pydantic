# 1. clone your fork and cd into the repo directory
git clone git@github.com:<your username>/pydantic.git
cd pydantic

# 2. Set up a virtualenv for running tests
virtualenv -p `which python3.7` env
source env/bin/activate
# (or however you prefer to setup a python environment, 3.6 will work too)

# 3. Install pydantic, dependencies and test dependencies
make install

# 4. Checkout a new branch and make your changes
git checkout -b my-new-feature-branch
# make your changes...

# 5. Fix formatting and imports
make format
# Pydantic uses black to enforce formatting and isort to fix imports
# (https://github.com/ambv/black, https://github.com/timothycrosley/isort)

# 6. Run tests and linting
make
# there are a few sub-commands in Makefile like `test`, `testcov` and `lint`
# which you might want to use, but generally just `make` should be all you need

# 7. Build documentation
make docs
# if you have changed the documentation make sure it builds successfully

# ... commit, push, and create your pull request
