"""Compatibility shim — proposal engine lives in labs.ch03_proposals."""

from labs.ch03_proposals.planner import plan_then_implement
from labs.ch03_proposals.reject_gates import ProposalRejectError, build_proposal

__all__ = ["ProposalRejectError", "build_proposal", "plan_then_implement"]
