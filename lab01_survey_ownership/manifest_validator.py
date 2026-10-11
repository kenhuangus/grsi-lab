"""Compatibility shim — modularity validation lives in labs.ch02_ownership."""

from labs.ch02_ownership.manifest import (  # noqa: F401
    REQUIRED_COMPONENT_FIELDS,
    validate_manifest_file,
    validate_modularity,
)
