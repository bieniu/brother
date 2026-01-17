#!/bin/bash

PYTHON_VERSION=3.14

python$PYTHON_VERSION -m pip install uv
python$PYTHON_VERSION -m uv venv venv --seed --python=$PYTHON_VERSION
source venv/bin/activate
pip install uv
uv pip install . .[dev]
prek install
