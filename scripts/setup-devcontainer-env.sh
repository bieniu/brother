#!/bin/bash

pip install --upgrade pip setuptools wheel
pip --disable-pip-version-check --no-cache-dir install -r requirements-dev.txt
pre-commit install
