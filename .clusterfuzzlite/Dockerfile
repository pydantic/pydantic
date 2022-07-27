FROM gcr.io/oss-fuzz-base/base-builder-python

COPY . $SRC/
WORKDIR $SRC/pydantic
COPY .clusterfuzzlite/build.sh $SRC/
