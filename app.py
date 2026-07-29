"""
app.py  ─  TCOE ID Generator · Flask Application
Nokia UATMN Master Database Integration
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from db import get_use_cases, generate_next_id, get_db_status
from network_mapping import get_network_code, NETWORK_OPTIONS
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ── SERVICE WORKER (root-scoped for PWA) ──────────────────────
@app.route("/sw.js")
def service_worker():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "sw.js",
        mimetype="application/javascript",
    )


# ── MAIN PAGE ─────────────────────────────────────────────────
@app.route("/")
def index():
    use_cases  = get_use_cases()
    db_status  = get_db_status()
    return render_template("index.html",
                           use_cases=use_cases,
                           network_options=NETWORK_OPTIONS,
                           db_status=db_status)


# ── API: DB STATUS ────────────────────────────────────────────
@app.route("/api/status")
def api_status():
    """Returns current DB connection state for the UI indicator."""
    return jsonify(get_db_status())


# ── API: GENERATE ID ──────────────────────────────────────────
@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    POST /api/generate
    Body: {
        "use_case":        "BCALL",
        "caller_network":  "4G",
        "receiver_network":"4G",
        "count":           1,
        "reserve":         false
    }
    Returns: {
        "ids":             ["BCALL009004--"],
        "network_code":    "009",
        "caller_network":  "4G",
        "receiver_network":"4G",
        ...
    }
    """
    data             = request.get_json(force=True)
    use_case         = data.get("use_case",         "").strip().upper()
    caller_network   = data.get("caller_network",   "").strip().upper()
    receiver_network = data.get("receiver_network", "").strip().upper()
    count            = int(data.get("count",   1))
    reserve          = bool(data.get("reserve", False))

    if not use_case:
        return jsonify({"error": "use_case is required"}), 400
    if not caller_network or not receiver_network:
        return jsonify({"error": "caller_network and receiver_network are required"}), 400

    network_code = get_network_code(caller_network, receiver_network)
    if network_code is None:
        return jsonify({
            "error": (f"No mapping defined for {caller_network} → {receiver_network}. "
                      "This combination will be added to network_mapping.py.")
        }), 400

    result = generate_next_id(use_case, network_code, count=count, reserve=reserve)
    if "error" in result:
        return jsonify(result), 500

    result["caller_network"]   = caller_network
    result["receiver_network"] = receiver_network
    result["network_code"]     = network_code
    return jsonify(result)


# ── API: HISTORY ──────────────────────────────────────────────
@app.route("/api/history")
def api_history():
    """GET /api/history?use_case=BCALL&limit=10"""
    from db import get_history
    use_case = request.args.get("use_case", "").strip().upper()
    limit    = int(request.args.get("limit", 10))
    return jsonify(get_history(use_case, limit))


# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    # use_reloader=False keeps the in-memory demo DB alive.
    # When DATABASE_URL points to a real DB this restriction is lifted.
    import config
    app.run(debug=True, port=5000, use_reloader=config.USE_DEMO_DATA is False)
