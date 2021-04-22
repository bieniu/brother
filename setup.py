#!/usr/bin/env python
from setuptools import setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="brother",
    version="1.0.0",
    author="Maciej Bieniek",
    description="Python wrapper for getting data from Brother laser and inkjet \
        printers via SNMP.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    url="https://github.com/bieniu/brother",
    license="Apache-2.0 License",
    packages=["brother"],
    python_requires=">=3.6",
    install_requires=list(val.strip() for val in open("requirements.txt")),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    setup_requires=("pytest-runner"),
    tests_require=list(val.strip() for val in open("requirements-test.txt")),
)
