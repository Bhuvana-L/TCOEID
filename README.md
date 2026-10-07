# TCOE ID Generator — Nokia UATMN

A Progressive Web App (PWA) for generating and tracking TCOE IDs against the Nokia UATMN Master Database.

---

## Overview

The TCOE ID Generator automates test case ID creation for Nokia's UATMN integration testing. It supports two call types — **Basic Call** (caller → receiver) and **Conference Call** (multi-participant) — and persists every generated ID to a database with full history.

**ID format:**

```
{USE_CASE}{9-digit block}--{DESCRIPTION}
```

The 9-digit block encodes the network combination code and a zero-padded sequence number:

```
BCALL000009072--4G_A_TO_4G_B_BASIC_CALL_B_REJECTS
│     │        │  └─ description
│     │        └─ separator
│     └─ 000009072 → network code 9 (4G→4G) + sequence 072
└─ use case
```

---

## Project Structure

```
tcoe-id-generator/
├── app.py               # Flask application, routes, API endpoints
├── db.py                # Universal database layer (SQLAlchemy)
├── config.py            # Single configuration file — edit this to connect your DB
├── network_mapping.py   # (Caller, Receiver) → 3-digit network code table
├── requirements.txt     # Python dependencies
├── demo.db              # SQLite demo database (auto-created)
├── static/
│   ├── css/style.css    # UI styles
│   ├── js/main.js       # Frontend logic (PWA, form handling, history)
│   ├── icons/           # PWA icons (192×192 and 512×512)
│   ├── manifest.json    # PWA manifest
│   └── sw.js            # Service worker
└── templates/
    └── index.html       # Jinja2 HTML template
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

With no `DATABASE_URL` configured the app runs automatically in **demo mode** using a local SQLite file (`demo.db`) pre-seeded with sample records.

---

## Connecting to Nokia's Database

**You only need to edit `config.py`.**

Set `DATABASE_URL` to the connection string for Nokia's UATMN database, then restart the app. Everything else — table discovery, column mapping, schema detection — is handled automatically.

```python
# config.py
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
```

If the connection succeeds, the app switches to Live DB mode. If it fails for any reason, the app falls back to demo mode automatically — nothing breaks.

### Supported database platforms

| Platform   | Example URL |
|------------|-------------|
| SQLite     | `sqlite:///C:/path/to/uatmn.db` |
| MySQL      | `mysql+pymysql://user:pass@host:3306/dbname` |
| PostgreSQL | `postgresql://user:pass@host:5432/dbname` |
| MS SQL     | `mssql+pyodbc://user:pass@host/dbname?driver=ODBC+Driver+17+for+SQL+Server` |
| Oracle     | `oracle+cx_oracle://user:pass@host:1521/?service_name=svc` |

Install the matching driver (e.g. `pip install pymysql`, `pip install psycopg2-binary`) in addition to `requirements.txt`.

### Optional: override the table name

```python
# config.py — leave "" for auto-detection
TCOE_TABLE = "tcoe_master"
```

### Optional: add custom column name hints

If Nokia's column names aren't in the default detection list, map them here:

```python
# config.py
EXTRA_COLUMN_HINTS = {
    "tcoe_id":  ["test_id"],
    "use_case": ["service_type"],
}
```

The app automatically detects these column roles by default:

| Role        | Recognised column names |
|-------------|------------------------|
| TCOE ID     | `tcoe_id`, `id`, `tcoe`, `identifier`, `test_case_id`, `tcoe_prefix` |
| Use Case    | `use_case`, `usecase`, `use_case_code`, `category`, `type`, `uc` |
| Sequence    | `sequence_number`, `sequence`, `seq`, `seq_number`, `number`, `num` |
| Network     | `network_type`, `network`, `net_type`, `nw_type`, `net`, `nw` |
| Description | `description`, `desc`, `name`, `title`, `remarks`, `detail` |

---

## Use Cases

| Code   | Description |
|--------|-------------|
| BCALL  | Basic Call |
| BARRG  | Call Barring |
| CHOLD  | Call Hold |
| CONFE  | Conference Call |
| PORTE  | Port-In / Port-Out |
| CFWDU  | Call Forward Unconditional |
| CFWDB  | Call Forward Busy |
| SMSMG  | SMS Mobile Originated |

---

## Network Combination Codes

Codes are looked up from `network_mapping.py` using the (Caller, Receiver) pair. Confirmed codes (001–019):

| Code | Combination         | Code | Combination         |
|------|---------------------|------|---------------------|
| 001  | 2G → 2G             | 011  | 5G → 4G             |
| 002  | 2G → 3G             | 012  | 5G → 5G             |
| 003  | 2G → 4G             | 013  | WiFi → 4G           |
| 004  | 2G → 5G             | 014  | 4G → WiFi           |
| 005  | 3G → 2G             | 015  | WiFi → WiFi         |
| 006  | 3G → 3G             | 016  | OtherOperator → 4G  |
| 007  | 3G → 4G             | 017  | 4G → OtherOperator  |
| 008  | 3G → 5G             | 018  | PortIn → 4G         |
| 009  | 4G → 4G ✓           | 019  | 4G → PortIn         |
| 010  | 4G → 5G             |      |                     |

Codes 020–049 cover the remaining combinations. To add or update a mapping, edit `network_mapping.py` only — no other file needs to change.

---

## API Reference

### `GET /`
Serves the main UI.

### `GET /api/status`
Returns the current database connection state.

```json
{ "demo_mode": true, "connected": false, "database_url": "demo" }
```

### `POST /api/generate`
Generates and reserves a TCOE ID.

**Basic Call:**
```json
{
  "use_case": "BCALL",
  "caller_network": "4G",
  "receiver_network": "4G",
  "description": "4G_A_TO_4G_B_BASIC_CALL"
}
```

**Conference Call:**
```json
{
  "use_case": "CONFE",
  "participants": ["4G", "5G", "WIFI"],
  "description": "3-Party Conference"
}
```

For conference calls, the first participant is treated as the caller and the last as the receiver when resolving the network code.

**Response:**
```json
{
  "ids": ["BCALL000009072--4G_A_TO_4G_B_BASIC_CALL"],
  "reserved": true,
  "use_case": "BCALL",
  "network": "009",
  "sequences": [72],
  "caller_network": "4G",
  "receiver_network": "4G",
  "network_code": "009"
}
```

### `GET /api/history?use_case=BCALL&limit=10`
Returns the last N records for a given use case.

---

## PWA Support

The app is installable as a Progressive Web App on both desktop and mobile. It registers a service worker for offline caching and includes a Web App Manifest with icons.

---

## Dependencies

| Package      | Version  | Purpose |
|--------------|----------|---------|
| Flask        | 3.1.3    | Web framework |
| SQLAlchemy   | 2.0.52   | Database abstraction layer |
| Werkzeug     | 3.1.8    | WSGI utilities |
| Jinja2       | 3.1.6    | HTML templating |

See `requirements.txt` for the full pinned list.
