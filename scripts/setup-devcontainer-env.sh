#!/bin/bash

pip install --upgrade pip setuptools wheel
pip --disable-pip-version-check --no-cache-dir install .[dev]
pip install -e .
prek install
