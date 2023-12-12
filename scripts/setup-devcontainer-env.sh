#!/bin/bash

pip3 install --upgrade pip setuptools wheel
pip3 --disable-pip-version-check --no-cache-dir install -r requirements-dev.txt
pre-commit install
