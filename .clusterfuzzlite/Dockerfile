FROM gcr.io/oss-fuzz-base/base-builder-python

COPY . $SRC/
WORKDIR pydantic
COPY .clusterfuzzlite/build.sh $SRC/
