#!/bin/bash

pip install --upgrade pip setuptools wheel
pip --disable-pip-version-check --no-cache-dir install .[test] .[dev]
pip install -e .
pre-commit install
