#!/bin/bash

if ! command -v uv >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if command -v python3.14 >/dev/null 2>&1; then
	PYTHON_VERSION=3.14
elif command -v python3.13 >/dev/null 2>&1; then
	PYTHON_VERSION=3.13
else
	echo "Error: neither python3.14 nor python3.13 is available in PATH" >&2
	exit 1
fi

uv sync --frozen --all-groups --python=$PYTHON_VERSION
uv run prek install
