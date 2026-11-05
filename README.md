# TCOE ID Generator — Nokia UATMN

A web-based tool for generating, reserving, and tracking TCOE test case IDs against the Nokia UATMN Master Database. Built as an installable Progressive Web App (PWA) with a Flask backend and a universal database layer that adapts to any SQL platform Nokia provides.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Running the Application](#3-running-the-application)
4. [Connecting to Nokia's Database](#4-connecting-to-nokias-database)
5. [Features](#5-features)
6. [How TCOE IDs Work](#6-how-tcoe-ids-work)
7. [Supported Use Cases](#7-supported-use-cases)
8. [Network Combination Codes](#8-network-combination-codes)
9. [API Reference](#9-api-reference)
10. [Architecture](#10-architecture)
11. [Security](#11-security)
12. [PWA Support](#12-pwa-support)
13. [Troubleshooting](#13-troubleshooting)
14. [Dependencies](#14-dependencies)

---

## 1. Prerequisites

Before installing, ensure the following are available on your system:

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| **Python** | 3.9+ | Tested on Python 3.12.8 |
| **pip** | 21.0+ | Comes bundled with Python |
| **Web browser** | Any modern browser | Chrome, Edge, Firefox, or Safari |

**Optional** — required only if connecting to a specific database platform (see [Section 4](#4-connecting-to-nokias-database)):

| Database Platform | Additional Driver | Install Command |
|--------------------|-------------------|-----------------|
| MySQL | PyMySQL | `pip install pymysql` |
| PostgreSQL | psycopg2 | `pip install psycopg2-binary` |
| MS SQL Server | pyodbc | `pip install pyodbc` |
| Oracle | cx_Oracle | `pip install cx_Oracle` |
| SQLite | *(none — built into Python)* | — |

No additional drivers are needed to run the application in demo mode (SQLite is included with Python by default).

---

## 2. Installation

### Step 1 — Download the project

Clone or download the project folder to your machine:

```bash
git clone https://github.com/Bhuvana-L/TCOEID.git
cd TCOEID
```

If you received the project as a ZIP archive, extract it and open a terminal in the project root folder.

### Step 2 — (Recommended) Create a virtual environment

A virtual environment keeps the project dependencies isolated from your system Python. This step is optional but strongly recommended:

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

If PowerShell blocks the activation script, run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, and all required sub-dependencies. The full list with pinned versions is in [Section 14](#14-dependencies).

### Step 4 — Install an optional database driver (only if needed)

If you are connecting to a real database (not demo mode), install the matching driver from the table in [Section 1](#1-prerequisites). For example:

```bash
pip install psycopg2-binary    # PostgreSQL
```

Skip this step if you are running in demo mode (SQLite, no driver needed).

### Step 5 — Verify the installation

Run the following to confirm all packages installed correctly:

```bash
python -c "import flask, sqlalchemy; print('Dependencies OK')"
```

You should see `Dependencies OK` printed with no errors.

---

## 3. Running the Application

### Start the server

From the project root folder:

```bash
python app.py
```

### Open in browser

Navigate to:

```
http://localhost:5000
```

The application is now running. If no `DATABASE_URL` is configured (see [Section 4](#4-connecting-to-nokias-database)), the app starts in **demo mode** using a local SQLite database (`demo.db`) that is automatically created and pre-seeded with sample records. No additional setup is required.

### Stop the server

Press `Ctrl + C` in the terminal where the server is running.

---

## 4. Connecting to Nokia's Database

To connect the application to Nokia's UATMN database, **only one file needs to be edited: `config.py`**. No other source code changes are required.

### Step 1 — Set the database URL

Open `config.py` and set `DATABASE_URL` to the connection string for Nokia's database:

```python
# config.py
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
```

### Step 2 — Restart the application

```bash
python app.py
```

The application will attempt to connect at startup. On success, it switches to live database mode. If the connection fails for any reason, it automatically falls back to demo mode — the application remains fully functional.

### Database URL formats by platform

| Platform | Connection String Example |
|----------|--------------------------|
| SQLite | `sqlite:///C:/path/to/uatmn.db` |
| MySQL | `mysql+pymysql://user:password@host:3306/dbname` |
| PostgreSQL | `postgresql://user:password@host:5432/dbname` |
| MS SQL Server | `mssql+pyodbc://user:password@host/dbname?driver=ODBC+Driver+17+for+SQL+Server` |
| Oracle | `oracle+cx_oracle://user:password@host:1521/?service_name=svc` |

### Optional configuration

**Override the table name** — if auto-detection picks the wrong table:

```python
# config.py — leave "" for auto-detection
TCOE_TABLE = "tcoe_master"
```

**Add custom column name hints** — if Nokia's column names do not match the defaults:

```python
# config.py
EXTRA_COLUMN_HINTS = {
    "tcoe_id":  ["test_id"],
    "use_case": ["service_type"],
}
```

### Auto-detected column names

The application inspects the database schema at startup and maps columns by common naming patterns. The following names are recognised automatically:

| Role | Recognised Column Names |
|------|------------------------|
| TCOE ID | `tcoe_id`, `id`, `tcoe`, `identifier`, `test_case_id`, `tcoe_prefix` |
| Use Case | `use_case`, `usecase`, `use_case_code`, `category`, `type`, `uc`, `service` |
| Sequence | `sequence_number`, `sequence`, `seq`, `seq_number`, `number`, `num`, `counter` |
| Network | `network_type`, `network`, `net_type`, `nw_type`, `net`, `nw`, `path` |
| Description | `description`, `desc`, `name`, `title`, `remarks`, `detail`, `summary` |

If a column is not found, it is treated as optional and the application continues to work with the columns it did detect.

---

## 5. Features

**ID Generation**
- One-click TCOE ID generation with automatic sequence numbering
- Duplicate prevention — every ID is checked against the database before insertion
- Thread-safe generation using a mutex lock to prevent race conditions under concurrent use
- Support for two call types: Basic Call (caller → receiver) and Conference Call (multi-participant)

**History & Filtering**
- Live history table showing the most recent records per use case
- Filter by use case (e.g. BCALL, CONFE) via dropdown
- Filter by network combination (e.g. 4G → 5G) via grouped dropdown
- Both filters can be combined, or set to "All" to view everything
- Network codes are displayed as readable labels (e.g. "4G → 4G") instead of raw codes

**Database Flexibility**
- Works with SQLite, MySQL, PostgreSQL, MS SQL Server, and Oracle
- Auto-detects the correct table and column names at startup by inspecting the schema
- Zero code changes required to switch databases — only `config.py` is edited
- Automatic fallback to a local demo database if the live connection is unavailable

**Progressive Web App**
- Installable on desktop and mobile devices
- Offline-capable via service worker caching
- Responsive UI that works on phones, tablets, and desktops

---

## 6. How TCOE IDs Work

Every generated ID follows a fixed, parseable format:

```
{USE_CASE}{9-digit-block}--{DESCRIPTION}
```

### Breakdown

```
BCALL000009072--4G_A_TO_4G_B_BASIC_CALL_B_REJECTS
│     │             │  └─ description (user-provided)
│     │             └─ separator
│     └─ 9-digit block = network code + sequence
└─ use case code
```

### The 9-digit block

The block encodes two values packed together:

1. **Network code** — converted to an integer (e.g. `"009"` → `9`)
2. **Sequence number** — zero-padded to 3 digits (e.g. `72` → `072`)

These are concatenated and then zero-padded to 9 digits total:

```
network_code = "009"  →  int = 9
sequence      = 72    →  "072"
concatenated  = "9" + "072" = "9072"
padded to 9   = "000009072"
```

### Example IDs

| ID | Use Case | Network | Sequence | Description |
|----|----------|---------|----------|-------------|
| `BCALL000009001--Basic_Call_4G_to_4G` | BCALL | 4G → 4G (009) | 1 | Basic_Call_4G_to_4G |
| `BARRG000009002--Barring_BOIC_4G` | BARRG | 4G → 4G (009) | 2 | Barring_BOIC_4G |
| `CONFE000007001--3-Party_Conference` | CONFE | 3G → 4G (007) | 1 | 3-Party_Conference |

### Conference call rule

For conference calls with multiple participants, the **first participant** is treated as the caller and the **last participant** as the receiver for the network code lookup. Middle participants do not affect the code. A single TCOE ID is generated for the entire conference.

---

## 7. Supported Use Cases

| Code | Description |
|------|-------------|
| BCALL | Basic Call |
| BARRG | Call Barring |
| CHOLD | Call Hold |
| CONFE | Conference Call |
| PORTE | Port-In / Port-Out |
| CFWDU | Call Forward Unconditional |
| CFWDB | Call Forward Busy |
| SMSMG | SMS Mobile Originated |

---

## 8. Network Combination Codes

Codes are defined in `network_mapping.py` and looked up using the (Caller, Receiver) pair. The following codes have been confirmed with Nokia:

| Code | Combination | Code | Combination |
|------|-------------|------|-------------|
| 001 | 2G → 2G | 011 | 5G → 4G |
| 002 | 2G → 3G | 012 | 5G → 5G |
| 003 | 2G → 4G | 013 | WiFi → 4G |
| 004 | 2G → 5G | 014 | 4G → WiFi |
| 005 | 3G → 2G | 015 | WiFi → WiFi |
| 006 | 3G → 3G | 016 | OtherOperator → 4G |
| 007 | 3G → 4G | 017 | 4G → OtherOperator |
| 008 | 3G → 5G | 018 | PortIn → 4G |
| 009 | 4G → 4G | 019 | 4G → PortIn |
| 010 | 4G → 5G | | |

Codes 020–049 cover the remaining 7 × 7 network combinations. To add or update a mapping, edit `network_mapping.py` only — no other file needs to change.

The seven supported network types are: **2G, 3G, 4G, 5G, WIFI, OTHER_OPERATOR, PORTIN**.

---

## 9. API Reference

### `GET /`
Serves the main application UI (HTML page).

---

### `GET /api/status`
Returns the current database connection state.

**Response:**
```json
{
  "demo_mode": true,
  "connected": false,
  "database_url": "demo"
}
```

---

### `POST /api/generate`
Generates and reserves a TCOE ID in the database.

**Basic Call request:**
```json
{
  "use_case": "BCALL",
  "caller_network": "4G",
  "receiver_network": "4G",
  "description": "4G_A_TO_4G_B_BASIC_CALL"
}
```

**Conference Call request:**
```json
{
  "use_case": "CONFE",
  "participants": ["4G", "5G", "WIFI"],
  "description": "3-Party Conference"
}
```

**Response (200 OK):**
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

**Error responses:**
- `400` — missing required fields, or no network mapping defined for the selected combination
- `500` — database error or duplicate ID detected

---

### `GET /api/history`
Returns the most recent TCOE ID records, optionally filtered.

**Parameters (all optional):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_case` | string | *(empty = all)* | Filter by use case code (e.g. `BCALL`) |
| `network` | string | *(empty = all)* | Filter by 3-digit network code (e.g. `009`) |
| `limit` | integer | 10 | Number of records to return (clamped to 1–100) |

**Example:**
```
GET /api/history?use_case=BCALL&network=009&limit=10
```

**Response:**
```json
[
  {
    "tcoe_id": "BCALL000009006--4G_TO_4G_BASIC_CALL",
    "use_case": "BCALL",
    "sequence": 6,
    "network": "009",
    "description": "4G_TO_4G_BASIC_CALL"
  }
]
```

---

## 10. Architecture

```
┌──────────────────────────────────────────────┐
│  Browser (PWA)                                │
│  HTML/CSS/JS  ·  Service Worker               │
└──────────────────┬───────────────────────────┘
                   │  HTTP / JSON
┌──────────────────▼───────────────────────────┐
│  Flask Application (app.py)                   │
│  Routes · API endpoints · Request handling   │
└──────┬───────────────────────┬───────────────┘
       │                       │
       │                       │
┌──────▼──────┐    ┌──────────▼────────────────┐
│ network_    │    │ db.py (SQLAlchemy)         │
│ mapping.py  │    │ Schema auto-detection      │
│ (Caller,    │    │ Thread-safe ID generation  │
│  Receiver)  │    │ Duplicate guard             │
│ → 3-digit   │    └──────────┬────────────────┘
│  code       │               │
└─────────────┘    ┌──────────▼────────────────┐
                   │  Database                   │
                   │  SQLite · MySQL · Postgres  │
                   │  MS SQL · Oracle            │
                   │  (or local demo fallback)    │
                   └─────────────────────────────┘
```

**Key files:**

| File | Responsibility |
|------|---------------|
| `app.py` | Flask web server, routes, API endpoints |
| `db.py` | Database engine, schema auto-detection, ID generation, history queries |
| `config.py` | Configuration — database URL, table name, column hints (the only file to edit) |
| `network_mapping.py` | (Caller, Receiver) → 3-digit network code lookup table |
| `templates/index.html` | Jinja2 HTML template for the UI |
| `static/js/main.js` | Frontend logic — form handling, API calls, history, PWA install |
| `static/css/style.css` | UI styling |
| `static/sw.js` | Service worker for offline caching |
| `static/manifest.json` | PWA web app manifest |

---

## 11. Security

- **SQL injection prevention** — all database queries use SQLAlchemy bound parameters. Column names are auto-detected from the database schema itself, never from user input.
- **XSS prevention** — all user-controlled text (descriptions, IDs) is HTML-escaped before being rendered in the browser. The history table and result display use an `escapeHtml` function on every interpolated value.
- **Duplicate prevention** — every generated ID is checked against the database before insertion. If a duplicate prefix already exists, the operation is rejected with an error.
- **Thread safety** — ID generation is wrapped in a mutex lock to prevent race conditions when multiple requests arrive simultaneously.
- **Input validation** — the `limit` parameter on the history API is validated and clamped to a range of 1–100. Non-numeric values fall back to the default.
- **Server-side enforcement** — `count` (always 1) and `reserve` (always true) are hardcoded in the API layer. A client cannot override these values to generate bulk IDs or skip database persistence.

---

## 12. PWA Support

The application is an installable Progressive Web App:

- **Web App Manifest** (`static/manifest.json`) — defines the app name, icons, theme color, and display mode
- **Service Worker** (`static/sw.js`) — caches static assets for offline use; API calls always go to the network for fresh data
- **Icons** — 192×192 and 512×512 PNG icons in `static/icons/`
- **Install** — click the "Install" button in the app, or use the browser's install prompt
- **Cache versioning** — the service worker cache is versioned (`tcoe-v13`). When the app is updated, the cache version is bumped so users automatically receive the latest assets on next load

---

## 13. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` from the project root |
| `ModuleNotFoundError: No module named 'pymysql'` | Install the driver for your database platform — see [Section 1](#1-prerequisites) |
| Page loads but says "demo mode" | `DATABASE_URL` in `config.py` is empty or the connection failed. Set the URL and restart |
| `Could not detect use_case or sequence column` | Nokia's column names do not match the defaults. Add them to `EXTRA_COLUMN_HINTS` in `config.py` |
| `No mapping defined for X → Y` | The selected (Caller, Receiver) pair is not in `network_mapping.py`. Add it and restart |
| Port 5000 already in use | Another process is using port 5000. Stop it, or change the port in the `app.run()` call at the bottom of `app.py` |
| Old UI appears after updating | The service worker is serving cached files. Hard-refresh the browser (`Ctrl+Shift+R`) or clear the browser cache |
| PowerShell blocks virtual environment activation | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## 14. Dependencies

All dependencies are pinned to specific versions in `requirements.txt` for reproducibility:

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.1.3 | Web framework (routing, request handling, templating) |
| SQLAlchemy | 2.0.52 | Database abstraction layer (engine, schema inspection, queries) |
| Werkzeug | 3.1.8 | WSGI utilities (used by Flask) |
| Jinja2 | 3.1.6 | HTML templating engine |
| click | 8.4.2 | CLI toolkit (used by Flask) |
| blinker | 1.9.0 | Signal/event library (used by Flask) |
| itsdangerous | 2.2.0 | Token signing (used by Flask) |
| MarkupSafe | 3.0.3 | HTML escaping utilities (used by Jinja2) |
| greenlet | 3.5.5 | Lightweight coroutines (used by SQLAlchemy) |

Install all at once:
```bash
pip install -r requirements.txt
```

---

## Project Structure

```
TCOEID/
├── app.py                 # Flask application — routes and API endpoints
├── db.py                  # Universal database layer — engine, schema detection, ID generation
├── config.py              # Configuration — edit this to connect to Nokia's database
├── network_mapping.py     # (Caller, Receiver) → 3-digit network code mapping table
├── requirements.txt       # Pinned Python dependencies
├── demo.db                # SQLite demo database (auto-created on first run)
├── static/
│   ├── css/
│   │   └── style.css       # Application styling
│   ├── js/
│   │   └── main.js         # Frontend logic — forms, history, PWA
│   ├── icons/
│   │   ├── icon-192.png    # PWA icon (192×192)
│   │   └── icon-512.png    # PWA icon (512×512)
│   ├── manifest.json       # PWA web app manifest
│   └── sw.js               # Service worker (offline caching)
└── templates/
    └── index.html          # Jinja2 HTML template
```

---

## License

This project is developed for Nokia UATMN internal use.
