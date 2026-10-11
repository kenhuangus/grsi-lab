"""Shim — canonical implementation lives in ``labs.ch10_ecosystem``."""

from labs.ch10_ecosystem.boundary_proxy import BoundaryProxy, EgressDenied

__all__ = ["BoundaryProxy", "EgressDenied"]
