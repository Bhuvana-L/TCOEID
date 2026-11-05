"""
network_mapping.py — Nokia UATMN Network Combination Codes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Maps (caller_network, receiver_network) → 3-digit code
used in TCOE ID generation.

ID format:  {USE_CASE}{NET_CODE}{SEQ}--
Example:    BCALL009004--  (BCALL · 4G→4G · 4th test case)

Networks:   2G · 3G · 4G · 5G · WIFI · OTHER_OPERATOR · PORTIN
Total:      7 × 7 = 49 combinations  (codes 001 – 049)

CONFIRMED by mentor (codes 001–019):
  001  2G→2G          006  3G→3G          011  5G→4G
  002  2G→3G          007  3G→4G          012  5G→5G
  003  2G→4G          008  3G→5G          013  WiFi→4G
  004  2G→5G          009  4G→4G  ✓       014  4G→WiFi
  005  3G→2G          010  4G→5G          015  WiFi→WiFi
                                           016  OtherOp→4G
                                           017  4G→OtherOp
                                           018  PortIn→4G
                                           019  4G→PortIn

Codes 020–049 follow the same pattern — update with Nokia's
official values once confirmed by your mentor.

Key format  : (CALLER, RECEIVER)  — both uppercased
Value format: zero-padded 3-digit string

To add / update a mapping, edit this file only.
No other file needs to change.
"""

NETWORK_MAPPING: dict[tuple[str, str], str] = {

    # ══════════════════════════════════════════════════════════
    #  2G  originating  (codes 001–007)
    # ══════════════════════════════════════════════════════════
    ("2G", "2G"):             "001",
    ("2G", "3G"):             "002",
    ("2G", "4G"):             "003",
    ("2G", "5G"):             "004",
    ("2G", "WIFI"):           "020",
    ("2G", "OTHER_OPERATOR"): "021",
    ("2G", "PORTIN"):         "022",

    # ══════════════════════════════════════════════════════════
    #  3G  originating  (codes 005–008 + new)
    # ══════════════════════════════════════════════════════════
    ("3G", "2G"):             "005",
    ("3G", "3G"):             "006",
    ("3G", "4G"):             "007",
    ("3G", "5G"):             "008",
    ("3G", "WIFI"):           "023",
    ("3G", "OTHER_OPERATOR"): "024",
    ("3G", "PORTIN"):         "025",

    # ══════════════════════════════════════════════════════════
    #  4G  originating  (codes 009–010, 014, 017, 019 + new)
    # ══════════════════════════════════════════════════════════
    ("4G", "2G"):             "026",
    ("4G", "3G"):             "027",
    ("4G", "4G"):             "009",   # ✓ Confirmed by mentor
    ("4G", "5G"):             "010",
    ("4G", "WIFI"):           "014",
    ("4G", "OTHER_OPERATOR"): "017",
    ("4G", "PORTIN"):         "019",

    # ══════════════════════════════════════════════════════════
    #  5G  originating  (codes 011–012 + new)
    # ══════════════════════════════════════════════════════════
    ("5G", "2G"):             "028",
    ("5G", "3G"):             "029",
    ("5G", "4G"):             "011",
    ("5G", "5G"):             "012",
    ("5G", "WIFI"):           "030",
    ("5G", "OTHER_OPERATOR"): "031",
    ("5G", "PORTIN"):         "032",

    # ══════════════════════════════════════════════════════════
    #  WIFI  originating  (codes 013, 015 + new)
    # ══════════════════════════════════════════════════════════
    ("WIFI", "2G"):             "033",
    ("WIFI", "3G"):             "034",
    ("WIFI", "4G"):             "013",
    ("WIFI", "5G"):             "067",
    ("WIFI", "WIFI"):           "015",
    ("WIFI", "OTHER_OPERATOR"): "036",
    ("WIFI", "PORTIN"):         "037",

    # ══════════════════════════════════════════════════════════
    #  OTHER_OPERATOR  originating  (code 016 + new)
    # ══════════════════════════════════════════════════════════
    ("OTHER_OPERATOR", "2G"):             "038",
    ("OTHER_OPERATOR", "3G"):             "039",
    ("OTHER_OPERATOR", "4G"):             "016",
    ("OTHER_OPERATOR", "5G"):             "040",
    ("OTHER_OPERATOR", "WIFI"):           "041",
    ("OTHER_OPERATOR", "OTHER_OPERATOR"): "042",
    ("OTHER_OPERATOR", "PORTIN"):         "043",

    # ══════════════════════════════════════════════════════════
    #  PORTIN  originating  (code 018 + new)
    # ══════════════════════════════════════════════════════════
    ("PORTIN", "2G"):             "044",
    ("PORTIN", "3G"):             "045",
    ("PORTIN", "4G"):             "018",
    ("PORTIN", "5G"):             "046",
    ("PORTIN", "WIFI"):           "047",
    ("PORTIN", "OTHER_OPERATOR"): "048",
    ("PORTIN", "PORTIN"):         "049",
}


def get_network_code(caller: str, receiver: str) -> str | None:
    """
    Return the 3-digit mapping code for the given caller/receiver pair.

    Args:
        caller:   Caller network  (case-insensitive).
        receiver: Receiver network (case-insensitive).

    Returns:
        Zero-padded 3-digit string (e.g. "009"), or None if not mapped.
    """
    key = (caller.strip().upper(), receiver.strip().upper())
    return NETWORK_MAPPING.get(key)

def get_network_pairs() -> list[dict]:
    return [{"code": code, "label": f"{c} → {r}"} 
            for (c, r), code in NETWORK_MAPPING.items()]


# ── Ordered list for UI dropdowns ─────────────────────────────
NETWORK_OPTIONS: list[str] = [
    "2G",
    "3G",
    "4G",
    "5G",
    "WIFI",
    "OTHER_OPERATOR",
    "PORTIN",
]


# ── Reverse mappings for UI dropdowns & history display ─────────
# code → "Caller → Receiver" label (used by the history table to show
# a readable network combination instead of the raw 3-digit code).
NETWORK_CODE_LABELS: dict[str, str] = {
    code: f"{caller} → {receiver}"
    for (caller, receiver), code in NETWORK_MAPPING.items()
}

# Network combinations grouped by caller network, for the history
# filter dropdown.  Each group is sorted by receiver network.
NETWORK_COMBO_GROUPS: dict[str, list[tuple[str, str]]] = {}
for _net in NETWORK_OPTIONS:
    NETWORK_COMBO_GROUPS[_net] = []
for (_caller, _receiver), _code in NETWORK_MAPPING.items():
    NETWORK_COMBO_GROUPS[_caller].append((_code, _receiver))
for _net in NETWORK_COMBO_GROUPS:
    NETWORK_COMBO_GROUPS[_net].sort(key=lambda x: x[1])
