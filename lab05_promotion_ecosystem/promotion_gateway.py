"""Shim — canonical implementation lives in ``labs.ch09_promotion``."""

from labs.ch09_promotion.promotion_gateway import PromotionError, promote, validate_token

__all__ = ["PromotionError", "promote", "validate_token"]
