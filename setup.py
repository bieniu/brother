#!/usr/bin/env python3
"""Setup file for brother module."""
from pathlib import Path

from setuptools import setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
VERSION = "1.2.2"

setup(
    name="brother",
    version=VERSION,
    author="Maciej Bieniek",
    description="Python wrapper for getting data from Brother laser and inkjet \
        printers via SNMP.",
    long_description=README_FILE.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/bieniu/brother",
    license="Apache-2.0 License",
    packages=["brother"],
    package_data={"brother": ["py.typed"]},
    zip_safe=True,
    platforms="any",
    python_requires=">=3.8",
    install_requires=list(val.strip() for val in open("requirements.txt")),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Typing :: Typed",
    ],
)
