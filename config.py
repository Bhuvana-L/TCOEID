"""
config.py  ─  THE ONLY FILE YOU EVER NEED TO TOUCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO CONNECT NOKIA'S UATMN DATABASE
──────────────────────────────────────
1. Paste the DATABASE_URL for whatever platform Nokia gives you.
2. Restart the app.  That's it.  Nothing else changes.

The app detects the connection automatically:
  • If DATABASE_URL points to a real, reachable database  → uses it, local OFF
  • If the connection fails or DATABASE_URL is not set     → falls back to local DB

You do NOT need to change USE_LOCAL_DATA manually.
You do NOT need to know the table name or column names in advance.
The app auto-discovers them at startup.

──────────────────────────────────────────────────────────────────────────────
DATABASE_URL FORMATS  (copy-paste the one that matches Nokia's platform)
──────────────────────────────────────────────────────────────────────────────

  SQLite      sqlite:///C:/path/to/uatmn.db
              sqlite:////absolute/unix/path/uatmn.db

  MySQL       mysql+pymysql://user:password@host:3306/dbname
              (pip install pymysql)

  PostgreSQL  postgresql://user:password@host:5432/dbname
              (pip install psycopg2-binary)

  MS SQL      mssql+pyodbc://user:password@host/dbname?driver=ODBC+Driver+17+for+SQL+Server
              (pip install pyodbc)

  Oracle      oracle+cx_oracle://user:password@host:1521/?service_name=svc
              (pip install cx_Oracle)

  MongoDB *   NOT supported natively — ask Nokia for an SQL view or
              use a MongoDB BI Connector that exposes a MySQL interface,
              then connect via mysql+pymysql://...

──────────────────────────────────────────────────────────────────────────────
COLUMN AUTO-DETECTION
──────────────────────────────────────────────────────────────────────────────
The app scans the Nokia table and maps columns by common name patterns.
Recognised column name patterns:

  TCOE ID column   : tcoe_id, id, tcoe, identifier, test_case_id, tcoe_prefix
  Use Case column  : use_case, usecase, use_case_code, category, type, uc
  Sequence column  : sequence_number, sequence, seq, seq_number, number, num
  Network column   : network_type, network, net_type, nw_type, net, nw
  Description col  : description, desc, name, title, remarks, detail

If Nokia's column names don't match any of the above, add them to
EXTRA_COLUMN_HINTS below — no other file needs changing.

──────────────────────────────────────────────────────────────────────────────
TABLE NAME
──────────────────────────────────────────────────────────────────────────────
Leave TCOE_TABLE = "" to let the app auto-detect the right table.
Set it explicitly only if auto-detection picks the wrong table.
"""

import os

# ── 1. DATABASE URL ────────────────────────────────────────────────────────
#
#  Set this to Nokia's DB URL.
#  Leave as "" (empty string) to stay in local mode.
#
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# ── 2. TABLE NAME  (optional) ──────────────────────────────────────────────
#
#  Leave "" → auto-detect.
#  Set explicitly if the wrong table is picked.
#
TCOE_TABLE: str = os.getenv("TCOE_TABLE", "")

# ── 3. EXTRA COLUMN NAME HINTS  (optional) ─────────────────────────────────
#
#  If Nokia uses unusual column names not in the default list above,
#  add them here.  Key = logical role, Value = actual column name(s).
#
#  Example:
#    EXTRA_COLUMN_HINTS = {
#        "tcoe_id":  ["test_id", "record_id"],
#        "use_case": ["service_type"],
#    }
#
EXTRA_COLUMN_HINTS: dict[str, list[str]] = {}

# ── INTERNAL — do not edit ─────────────────────────────────────────────────
#  USE_LOCAL_DATA is set automatically by db.py based on whether
#  DATABASE_URL is set AND the connection succeeds.
#  You never need to touch this flag.
USE_LOCAL_DATA: bool = not bool(DATABASE_URL.strip())
