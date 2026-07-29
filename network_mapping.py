"""
network_mapping.py — Nokia UATMN Network Combination Codes
──────────────────────────────────────────────────────────
Maps (caller_network, receiver_network) tuples to a 3-digit
network mapping code used in TCOE ID generation.

This file is intentionally kept separate so the full Nokia
mapping table can be dropped in here without touching any
other application logic.

Key format  : (CALLER, RECEIVER)  — both values uppercased
Value format: zero-padded 3-digit string, e.g. "001"

To add a new mapping, simply append an entry to the dict.
"""

NETWORK_MAPPING: dict[tuple[str, str], str] = {
    # ── 2G originating ────────────────────────
    ("2G",             "2G"):             "001",
    ("2G",             "3G"):             "002",
    ("2G",             "4G"):             "003",
    ("2G",             "5G"):             "004",

    # ── 3G originating ────────────────────────
    ("3G",             "2G"):             "005",
    ("3G",             "3G"):             "006",
    ("3G",             "4G"):             "007",
    ("3G",             "5G"):             "008",

    # ── 4G originating ────────────────────────
    ("4G",             "4G"):             "009",   # Confirmed by mentor
    ("4G",             "5G"):             "010",
    ("4G",             "WIFI"):           "014",
    ("4G",             "OTHER_OPERATOR"): "017",
    ("4G",             "PORTIN"):         "019",

    # ── 5G originating ────────────────────────
    ("5G",             "4G"):             "011",
    ("5G",             "5G"):             "012",

    # ── WiFi originating ──────────────────────
    ("WIFI",           "4G"):             "013",
    ("WIFI",           "WIFI"):           "015",

    # ── Other Operator originating ────────────
    ("OTHER_OPERATOR", "4G"):             "016",

    # ── Port-In originating ───────────────────
    ("PORTIN",         "4G"):             "018",
}


def get_network_code(caller: str, receiver: str) -> str | None:
    """
    Return the mapping code for the given caller/receiver pair.

    Args:
        caller:   Caller network string (case-insensitive).
        receiver: Receiver network string (case-insensitive).

    Returns:
        3-digit string code, or None if the combination is not mapped.
    """
    key = (caller.strip().upper(), receiver.strip().upper())
    return NETWORK_MAPPING.get(key)


# Ordered list used to populate dropdowns in the UI
NETWORK_OPTIONS: list[str] = [
    "2G",
    "3G",
    "4G",
    "5G",
    "WIFI",
    "OTHER_OPERATOR",
    "PORTIN",
]
