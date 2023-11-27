#!/bin/bash

python3.10 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements-dev.txt
pre-commit install
