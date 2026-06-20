<!-- CLAUDE.md is a symlink to this file — edit only AGENTS.md -->
# Instructions for AI Agents (Copilot, Claude, Codex)

## Repository context

- This repository is a Python async SNMP wrapper for Brother laser and inkjet printers
- The publishable package is `brother` (PyPI name: `brother`)
- The public API surface is the `Brother` class in `brother/__init__.py`, the `BrotherSensors` dataclass in `brother/model.py`, and exceptions in `brother/exceptions.py`

## Project layout

```text
brother/
├── __init__.py    # Main Brother class — SNMP client, factory method, async_update()
├── const.py       # OID mappings, printer type constants, value/character-set mappings
├── exceptions.py  # BrotherError (base), SnmpError, UnsupportedModelError, MethodNotSupportedError
├── model.py       # BrotherSensors frozen dataclass (50+ sensor fields)
└── utils.py       # SNMP engine init, RFC 2579 DateAndTime codec, hex helpers

tests/
├── conftest.py       # Fixtures (brother_with_request_args, snapshot)
├── test_init.py      # All model-specific and edge-case tests
├── test_exceptions.py
├── test_utils.py
├── fixtures/         # JSON SNMP response fixtures per printer model
└── snapshots/        # syrupy snapshot files
```

## Python and environment

- Target Python: >=3.13 (also tested on 3.14)
- Use the local venv in `./.venv`
- `scripts/setup-local-env.sh` creates the venv, installs `uv`, then installs all dependency groups
- Package manager: `uv` — dependencies declared in `pyproject.toml`

## Linting, formatting, typing

```bash
uv sync --group dev
uv run ruff check .              # lint
uv run ruff check . --fix        # lint with auto-fix
uv run ruff format .             # format
uv run ruff format --check .     # check formatting without changes
uv run ty check brother          # type check
```

## Testing

```bash
uv sync --group test
uv run pytest --timeout=30 --cov=brother --cov-report=xml --error-for-skips   # full suite
uv run pytest tests/test_init.py::test_hl_l2340dw_model                        # single test
uv run pytest --snapshot-update                                                 # update syrupy snapshots
```

- SNMP calls are mocked via fixtures; never hit a real printer in tests
- Snapshots use `syrupy` (`tests/snapshots/`) — update with `--snapshot-update` when `BrotherSensors` fields change
- Update both snapshots and JSON fixtures together when response shapes change
- `freezegun` is used for time-sensitive tests (uptime, datetime fields)

## Architecture and key patterns

**Client lifecycle**: `Brother` is instantiated via the async factory method `Brother.create(host, printer_type, ipv6, model)`, which calls `initialize()` to probe the printer OID support and determine whether it is a laser or ink model.

**SNMP layer**: All printer queries go through `pysnmp`. The SNMP engine is created once in `utils.py` (with MIB caching) and reused across calls. `async_update()` fetches all relevant OIDs, then maps raw values through `const.py` dictionaries into a `BrotherSensors` dataclass via `dacite.from_dict()`.

**OID and value mapping**: All SNMP OIDs, printer types, supported/unsupported model lists, maintenance-level maps, and character-set maps live in `brother/const.py`. Adding support for a new printer model typically means updating this file and adding a fixture + snapshot in tests.

**Model**: `BrotherSensors` is a frozen dataclass with optional fields for every sensor the library can read. Fields missing from a printer's SNMP response remain `None`.

**Character sets**: Printer status strings may be encoded in UTF-8, Latin-2, Cyrillic, or Roman-8. Decoding is handled in `brother/__init__.py` using mapping tables from `const.py`.

## Implementation guidelines

- Keep all I/O async
- All new OIDs, constants, and value mappings belong in `brother/const.py`
- Preserve the `BrotherSensors` public field names; removing or renaming a field is a breaking change
- Use lazy logging: `_LOGGER.debug("msg %s", value)` — never f-strings in log calls
- Prefer specific exception types over the base `BrotherError`
- Avoid very long docstrings; one-line docstrings preferred, three lines at most
