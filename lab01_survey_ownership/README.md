# Lab 01 (legacy shim) — Survey / Ownership

Chapter-aligned homes:

- Survey taxonomy + keep/revert: `examples/ch01/`
- Ownership manifests, locked writes, freeze, blast: `labs/ch02_ownership/`

This package re-exports those modules for older import paths.

```bash
pytest -q labs/ch02_ownership/tests tests/test_locked_path.py
```
