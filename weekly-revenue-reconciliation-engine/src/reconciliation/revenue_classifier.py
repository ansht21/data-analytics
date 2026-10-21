"""Status -> financial bucket mapper (single source of truth)."""

from __future__ import annotations

BUCKET_LABELS = (
    "Net Realized",
    "Cancellation Leakage",
    "Return Leakage",
    "Loss Leakage",
    "In-Transit",
    "Pending",
    "Unmapped",
)

# Canonical fallback map (overridden by settings.yaml buckets when present).
_DEFAULT_MAP: dict[str, list[str]] = {
    "Net Realized": ["Shipped - Delivered to Buyer"],
    "Cancellation Leakage": ["Cancelled"],
    "Return Leakage": [
        "Shipped - Returned to Seller",
        "Shipped - Returning to Seller",
        "Shipped - Rejected by Buyer",
    ],
    "Loss Leakage": ["Shipped - Lost in Transit", "Shipped - Damaged"],
    "In-Transit": ["Shipped", "Shipped - Picked Up", "Shipped - Out for Delivery", "Shipping"],
    "Pending": ["Pending", "Pending - Waiting for Pick Up"],
}


def build_lookup(buckets: dict[str, list[str]] | None = None) -> dict[str, str]:
    """Build a ``{status: bucket}`` lookup from config (or defaults).

    Args:
        buckets: Optional ``{bucket: [statuses]}`` mapping from settings.

    Returns:
        Flat ``{status: bucket}`` dictionary.
    """
    source = buckets or _DEFAULT_MAP
    lookup: dict[str, str] = {}
    for bucket, statuses in source.items():
        for status in statuses or []:
            lookup[str(status)] = bucket
    return lookup


def classify_status(status: str, buckets: dict[str, list[str]] | None = None) -> str:
    """Classify one raw Amazon ``Status`` into a financial bucket.

    Args:
        status: Raw status string.
        buckets: Optional config override mapping.

    Returns:
        Bucket label, or ``"Unmapped"`` for unknown statuses.
    """
    return build_lookup(buckets).get(str(status), "Unmapped")
