"""
db.py  ─  Universal database layer for TCOE ID Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW IT WORKS
────────────
1.  At startup, reads DATABASE_URL from config.py.
2.  If DATABASE_URL is set → tries to connect to the real DB.
       Success → uses real DB, demo mode OFF.
       Failure → logs a warning, falls back to demo DB automatically.
3.  If DATABASE_URL is empty → demo mode ON immediately.

Nokia's table/column names are auto-discovered by inspecting the schema.
Nothing in this file needs to change regardless of the DB platform.

SUPPORTED PLATFORMS  (via SQLAlchemy)
    SQLite · MySQL · PostgreSQL · MS SQL Server · Oracle · and more
"""

import os
import threading
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import QueuePool, StaticPool

import config                          # imported as module so USE_DEMO_DATA
                                       # can be mutated at runtime

logger = logging.getLogger(__name__)
_lock  = threading.Lock()

# ──────────────────────────────────────────────────────────────
#  DEMO SEED DATA
#  ID format: {USE_CASE}{NET_CODE_3}{SEQ_3}--
#  e.g. BCALL009004-- = BCALL · 4G→4G (009) · 4th test case
# ──────────────────────────────────────────────────────────────

_DEMO_ROWS = [
    # (tcoe_id,             use_case, network, seq, description)
    # ID format: {USE_CASE}{zfill(9: int(NET)+SEQ_3)}--{desc}
    # e.g. code=009,seq=1 → 9+"001"="9001" → zfill(9)="000009001"
    # → BCALL000009001--Basic Call 4G→4G VoLTE

    # ── BCALL (Basic Call) ─────────────────────────────────────
    ("BCALL000001001--", "BCALL", "001", 1, "Basic Call 2G→2G"),
    ("BCALL000002001--", "BCALL", "002", 1, "Basic Call 2G→3G"),
    ("BCALL000003001--", "BCALL", "003", 1, "Basic Call 2G→4G"),
    ("BCALL000004001--", "BCALL", "004", 1, "Basic Call 2G→5G"),
    ("BCALL000005001--", "BCALL", "005", 1, "Basic Call 3G→2G"),
    ("BCALL000006001--", "BCALL", "006", 1, "Basic Call 3G→3G"),
    ("BCALL000007001--", "BCALL", "007", 1, "Basic Call 3G→4G"),
    ("BCALL000008001--", "BCALL", "008", 1, "Basic Call 3G→5G"),
    ("BCALL000009001--", "BCALL", "009", 1, "Basic Call 4G→4G VoLTE"),
    ("BCALL000009002--", "BCALL", "009", 2, "Basic Call 4G→4G VoLTE MO"),
    ("BCALL000009003--", "BCALL", "009", 3, "Basic Call 4G→4G MT"),
    ("BCALL000010001--", "BCALL", "010", 1, "Basic Call 4G→5G"),
    ("BCALL000011001--", "BCALL", "011", 1, "Basic Call 5G→4G"),
    ("BCALL000012001--", "BCALL", "012", 1, "Basic Call 5G→5G NR"),
    ("BCALL000013001--", "BCALL", "013", 1, "Basic Call WiFi→4G"),
    ("BCALL000014001--", "BCALL", "014", 1, "Basic Call 4G→WiFi"),
    ("BCALL000015001--", "BCALL", "015", 1, "Basic Call WiFi→WiFi"),
    ("BCALL000016001--", "BCALL", "016", 1, "Basic Call OtherOp→4G"),
    ("BCALL000017001--", "BCALL", "017", 1, "Basic Call 4G→OtherOp"),
    ("BCALL000018001--", "BCALL", "018", 1, "Basic Call PortIn→4G"),
    ("BCALL000019001--", "BCALL", "019", 1, "Basic Call 4G→PortIn"),

    # ── BARRG (Call Barring) ───────────────────────────────────
    ("BARRG000009001--", "BARRG", "009", 1, "Barring BAIC 4G→4G"),
    ("BARRG000009002--", "BARRG", "009", 2, "Barring BOIC 4G→4G"),
    ("BARRG000009003--", "BARRG", "009", 3, "Barring ODB  4G→4G"),
    ("BARRG000012001--", "BARRG", "012", 1, "Barring BAIC 5G→5G"),
    ("BARRG000013001--", "BARRG", "013", 1, "Barring WiFi→4G"),
    ("BARRG000016001--", "BARRG", "016", 1, "Barring OtherOp→4G"),

    # ── CHOLD (Call Hold) ──────────────────────────────────────
    ("CHOLD000009001--", "CHOLD", "009", 1, "Call Hold 4G→4G"),
    ("CHOLD000009002--", "CHOLD", "009", 2, "Call Hold 4G→4G Resume"),
    ("CHOLD000010001--", "CHOLD", "010", 1, "Call Hold 4G→5G"),
    ("CHOLD000012001--", "CHOLD", "012", 1, "Call Hold 5G→5G"),
    ("CHOLD000013001--", "CHOLD", "013", 1, "Call Hold WiFi→4G"),
    ("CHOLD000015001--", "CHOLD", "015", 1, "Call Hold WiFi→WiFi"),

    # ── CONFE (Conference Call) ────────────────────────────────
    ("CONFE000007001--", "CONFE", "007", 1, "3-Party Conference 3G→4G"),
    ("CONFE000009001--", "CONFE", "009", 1, "3-Party Conference 4G→4G"),
    ("CONFE000009002--", "CONFE", "009", 2, "3-Party Conference 4G→4G Add"),
    ("CONFE000012001--", "CONFE", "012", 1, "3-Party Conference 5G→5G"),
    ("CONFE000013001--", "CONFE", "013", 1, "3-Party Conference WiFi→4G"),
    ("CONFE000015001--", "CONFE", "015", 1, "3-Party Conference WiFi→WiFi"),

    # ── PORTE (Port-In / Port-Out) ─────────────────────────────
    ("PORTE000018001--", "PORTE", "018", 1, "Port-In Basic PortIn→4G"),
    ("PORTE000018002--", "PORTE", "018", 2, "Port-In Cancel PortIn→4G"),
    ("PORTE000019001--", "PORTE", "019", 1, "Port-In Validation 4G→PortIn"),
    ("PORTE000019002--", "PORTE", "019", 2, "Port-Out Confirm 4G→PortIn"),

    # ── CFWDU (Call Forward Unconditional) ─────────────────────
    ("CFWDU000009001--", "CFWDU", "009", 1, "CFU Activate 4G→4G"),
    ("CFWDU000009002--", "CFWDU", "009", 2, "CFU Deactivate 4G→4G"),
    ("CFWDU000010001--", "CFWDU", "010", 1, "CFU Register 4G→5G"),
    ("CFWDU000012001--", "CFWDU", "012", 1, "CFU Activate 5G→5G"),
    ("CFWDU000013001--", "CFWDU", "013", 1, "CFU Activate WiFi→4G"),

    # ── CFWDB (Call Forward Busy) ──────────────────────────────
    ("CFWDB000009001--", "CFWDB", "009", 1, "CFB Activate 4G→4G"),
    ("CFWDB000009002--", "CFWDB", "009", 2, "CFB Deactivate 4G→4G"),
    ("CFWDB000012001--", "CFWDB", "012", 1, "CFB Activate 5G→5G"),
    ("CFWDB000015001--", "CFWDB", "015", 1, "CFB Activate WiFi→WiFi"),

    # ── SMSMG (SMS Mobile Originated) ─────────────────────────
    ("SMSMG000007001--", "SMSMG", "007", 1, "SMS MO 3G→4G"),
    ("SMSMG000009001--", "SMSMG", "009", 1, "SMS MO 4G→4G VoLTE"),
    ("SMSMG000012001--", "SMSMG", "012", 1, "SMS MO 5G→5G NR"),
    ("SMSMG000013001--", "SMSMG", "013", 1, "SMS MO WiFi→4G"),
    ("SMSMG000016001--", "SMSMG", "016", 1, "SMS MO OtherOp→4G"),
]


def _seed_demo(engine) -> None:
    """Create the demo table and insert sample rows (idempotent)."""
    with engine.begin() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS tcoe_master (
                tcoe_id         TEXT PRIMARY KEY,
                use_case        TEXT NOT NULL,
                network_type    TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                description     TEXT
            )
        """))
        c.execute(text("""
            INSERT OR IGNORE INTO tcoe_master
                (tcoe_id, use_case, network_type, sequence_number, description)
            VALUES (:a, :b, :c, :d, :e)
        """), [{"a": r[0], "b": r[1], "c": r[2], "d": r[3], "e": r[4]}
               for r in _DEMO_ROWS])
    logger.info("Demo DB seeded — %d rows available.", len(_DEMO_ROWS))


# ──────────────────────────────────────────────────────────────
#  ENGINE  —  auto-detect real DB vs demo
# ──────────────────────────────────────────────────────────────

_engine = None


def _build_real_engine(url: str):
    """Create and *test* a SQLAlchemy engine. Returns engine or raises."""
    engine = create_engine(
        url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    # Actually open a connection to confirm the DB is reachable
    with engine.connect() as c:
        c.execute(text("SELECT 1"))
    return engine


def _build_demo_engine():
    """Create the file-based SQLite demo engine and seed it."""
    db_path = os.path.join(os.path.dirname(__file__), "demo.db")
    engine  = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    _seed_demo(engine)
    return engine


def _get_engine():
    global _engine
    if _engine is not None:
        return _engine

    url = config.DATABASE_URL.strip()

    if url:
        # A real URL is configured — try it
        logger.info("Attempting connection to real database...")
        try:
            _engine = _build_real_engine(url)
            config.USE_DEMO_DATA = False          # real DB is live
            logger.info("✅  Connected to real database: %s",
                        url.split("@")[-1])       # log host only, not credentials
        except (OperationalError, SQLAlchemyError, Exception) as exc:
            logger.warning(
                "⚠️  Could not connect to '%s': %s\n"
                "    Falling back to demo database automatically.",
                url.split("@")[-1], exc
            )
            config.USE_DEMO_DATA = True
            _engine = _build_demo_engine()
    else:
        # No URL configured — use demo
        config.USE_DEMO_DATA = True
        logger.info("No DATABASE_URL set — running in demo mode.")
        _engine = _build_demo_engine()

    return _engine


@contextmanager
def _conn():
    with _get_engine().connect() as c:
        yield c


# Initialise eagerly at import time so the DB is ready before
# the first HTTP request arrives.
_get_engine()


# ──────────────────────────────────────────────────────────────
#  SCHEMA AUTO-DETECTION
#  Inspects whatever table Nokia's DB has and maps column roles
#  by matching common naming patterns.
# ──────────────────────────────────────────────────────────────

_schema_cache: dict = {}

# Default candidate column names per logical role
_CANDIDATE_COLS: dict[str, list[str]] = {
    "tcoe_id":     ["tcoe_id", "id", "tcoe", "identifier",
                    "test_case_id", "tcoe_prefix"],
    "use_case":    ["use_case", "usecase", "use_case_code",
                    "category", "type", "uc", "service"],
    "sequence":    ["sequence_number", "sequence", "seq",
                    "seq_number", "number", "num", "counter"],
    "network":     ["network_type", "network", "net_type",
                    "nw_type", "net", "nw", "path"],
    "description": ["description", "desc", "name", "title",
                    "remarks", "detail", "summary"],
}


def _merged_candidates() -> dict[str, list[str]]:
    """Merge default candidates with any extra hints from config."""
    merged = {k: list(v) for k, v in _CANDIDATE_COLS.items()}
    for role, extras in config.EXTRA_COLUMN_HINTS.items():
        if role in merged:
            merged[role] = extras + merged[role]   # extras take priority
        else:
            merged[role] = extras
    return merged


def _detect_schema() -> dict:
    """
    Inspect the connected database and map logical column roles to
    the actual column names Nokia's table uses.  Result is cached.
    """
    global _schema_cache
    if _schema_cache:
        return _schema_cache

    insp   = inspect(_get_engine())
    tables = insp.get_table_names()

    # ── Find the right table ───────────────────────────────────
    table_name: str | None = None
    tcoe_table = config.TCOE_TABLE.strip()

    if tcoe_table and tcoe_table in tables:
        table_name = tcoe_table                    # explicit config wins
    else:
        # Pattern-match on table name
        for t in tables:
            if any(kw in t.lower()
                   for kw in ("tcoe", "test_case", "uatmn", "testcase",
                               "master", "test_id")):
                table_name = t
                break
        if table_name is None and tables:
            table_name = tables[0]                 # last resort: first table

    if not table_name:
        raise RuntimeError(
            "No tables found in the database. "
            "Check DATABASE_URL and database permissions."
        )

    # ── Map columns ────────────────────────────────────────────
    actual_cols = {
        c["name"].lower(): c["name"]
        for c in insp.get_columns(table_name)
    }
    candidates = _merged_candidates()
    mapping: dict = {"table": table_name}

    for role, names in candidates.items():
        for name in names:
            if name.lower() in actual_cols:
                mapping[role] = actual_cols[name.lower()]
                break
        else:
            mapping[role] = None          # column not found — optional

    mode = "DEMO" if config.USE_DEMO_DATA else "LIVE"
    logger.info("[%s] Schema → table=%s  cols=%s",
                mode, table_name,
                {k: v for k, v in mapping.items() if k != "table"})
    _schema_cache = mapping
    return mapping


# ──────────────────────────────────────────────────────────────
#  PUBLIC API
# ──────────────────────────────────────────────────────────────

def get_use_cases() -> list[str]:
    """Return distinct use-case codes for the dropdown."""
    try:
        s   = _detect_schema()
        col = s.get("use_case")
        if not col:
            return _default_use_cases()
        with _conn() as c:
            rows = c.execute(
                text(f"SELECT DISTINCT {col} FROM {s['table']} ORDER BY {col}")
            ).fetchall()
        return [r[0] for r in rows if r[0]]
    except Exception as e:
        logger.error("get_use_cases failed: %s", e)
        return _default_use_cases()


def generate_next_id(use_case: str, network_code: str,
                     count: int = 1, reserve: bool = False,
                     description: str = "") -> dict:
    """
    Thread-safe TCOE ID generation.

    ID format:  {USE_CASE}{9-digit-sequence}--{DESCRIPTION}
      USE_CASE   : e.g. BCALL
      9-digit seq: global sequence per use_case, zero-padded to 9
      DESCRIPTION: user-supplied text appended after --

    Examples:
      BCALL000009072--4G_A_TO_4G_B_BASIC_CALL_B_REJECTS
      BARRG000009001--4G_A_BARRING_BAIC
    """
    with _lock:
        try:
            s       = _detect_schema()
            table   = s["table"]
            uc_col  = s.get("use_case")
            seq_col = s.get("sequence")
            id_col  = s.get("tcoe_id")
            net_col = s.get("network")
            desc_col = s.get("description")

            if not uc_col or not seq_col:
                return {"error":
                        "Could not detect use_case or sequence column. "
                        "Add column hints to EXTRA_COLUMN_HINTS in config.py."}

            # Global sequence per use_case (not per network)
            with _conn() as c:
                row = c.execute(
                    text(f"SELECT MAX(CAST({seq_col} AS INTEGER)) "
                         f"FROM  {table} "
                         f"WHERE UPPER({uc_col}) = :uc"),
                    {"uc": use_case.upper()},
                ).fetchone()

            max_seq   = int(row[0]) if row and row[0] is not None else 0
            next_seqs = list(range(max_seq + 1, max_seq + 1 + count))

            # ID format: {USE_CASE}{9-digit-block}--{DESCRIPTION}
            #
            # The 9-digit block encodes both network code and sequence:
            #   int(network_code) concatenated with SEQ zero-padded to 3
            #   then the whole thing zero-padded to 9 digits.
            #
            # Example: network_code="009", seq=72
            #   → str(9) + "072" = "9072" → zfill(9) → "000009072"
            #   → BCALL000009072--4G_TO_4G_REJECTS
            #
            net_int = int(network_code)   # "009" → 9, strips leading zeros

            desc_clean = description.strip()
            ids = []
            for sq in next_seqs:
                block = f"{net_int}{str(sq).zfill(3)}"   # e.g. "9" + "072" = "9072"
                block = block.zfill(9)                    # → "000009072"
                full  = f"{use_case}{block}--"
                if desc_clean:
                    full += desc_clean
                ids.append(full)

            # Prefix used for duplicate check (without description)
            id_prefixes = [
                f"{use_case}{(str(int(network_code)) + str(sq).zfill(3)).zfill(9)}--"
                for sq in next_seqs
            ]

            # Duplicate guard on the prefix part
            if id_col:
                with _conn() as c:
                    for prefix in id_prefixes:
                        if c.execute(
                            text(f"SELECT 1 FROM {table} "
                                 f"WHERE {id_col} LIKE :tid"),
                            {"tid": prefix + "%"},
                        ).fetchone():
                            return {"error":
                                    f"Duplicate detected: {prefix} already exists."}

            # Insert rows (reserve always writes; non-reserve writes too to persist)
            if id_col and uc_col and seq_col:
                with _get_engine().begin() as c:
                    for full_id, prefix, sq in zip(ids, id_prefixes, next_seqs):
                        row_data = {
                            id_col:  full_id,    # store full id including description
                            uc_col:  use_case,
                            seq_col: sq,
                        }
                        if net_col:
                            row_data[net_col] = network_code
                        if desc_col and desc_clean:
                            row_data[desc_col] = desc_clean
                        cols = ", ".join(row_data)
                        vals = ", ".join(f":{k}" for k in row_data)
                        c.execute(
                            text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"),
                            row_data,
                        )

            return {
                "ids":         ids,
                "reserved":    reserve,
                "use_case":    use_case,
                "network":     network_code,
                "sequences":   next_seqs,
                "description": desc_clean,
            }

        except Exception as e:
            logger.error("generate_next_id error: %s", e)
            return {"error": str(e)}


def get_history(use_case: str = "", network: str = "", limit: int = 10) -> list[dict]:
    """Return the last N TCOE IDs, optionally filtered by use_case and/or network."""
    try:
        s        = _detect_schema()
        table    = s["table"]
        uc_col   = s.get("use_case")
        id_col   = s.get("tcoe_id")
        seq_col  = s.get("sequence")
        net_col  = s.get("network")
        desc_col = s.get("description")

        if not uc_col or not id_col:
            return []

        order_col = seq_col or id_col
        desc_expr = desc_col if desc_col else "''"

        where_clauses = []
        params: dict = {"lim": limit}
        if use_case:
            where_clauses.append(f"UPPER({uc_col}) = :uc")
            params["uc"] = use_case.upper()
        if network and net_col:
            where_clauses.append(f"{net_col} = :net")
            params["net"] = network
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        with _conn() as c:
            rows = c.execute(text(f"""
                SELECT {id_col},
                       {uc_col},
                       {seq_col   if seq_col  else 'NULL'},
                       {net_col   if net_col  else "''"},
                       {desc_expr}
                FROM   {table}
                {where_sql}
                ORDER  BY CAST({order_col} AS INTEGER) DESC
                LIMIT  :lim
            """), params).fetchall()

        return [{"tcoe_id":     r[0], "use_case":    r[1],
                 "sequence":    r[2], "network":     r[3],
                 "description": r[4]}
                for r in rows]

    except Exception as e:
        logger.error("get_history error: %s", e)
        return []


def get_db_status() -> dict:
    """
    Return the current DB connection status.
    Called by the /api/status endpoint for the UI indicator.
    """
    return {
        "demo_mode":    config.USE_DEMO_DATA,
        "connected":    not config.USE_DEMO_DATA,
        "database_url": (config.DATABASE_URL.split("@")[-1]
                         if config.DATABASE_URL and "@" in config.DATABASE_URL
                         else ("demo" if config.USE_DEMO_DATA else config.DATABASE_URL)),
    }


# ──────────────────────────────────────────────────────────────
#  FALLBACK DEFAULTS
# ──────────────────────────────────────────────────────────────

def _default_use_cases() -> list[str]:
    return ["BARRG", "BCALL", "CFWDB", "CFWDU",
            "CHOLD", "CONFE", "PORTE", "SMSMG"]
