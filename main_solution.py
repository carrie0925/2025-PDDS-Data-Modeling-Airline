from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os

# -------------------------
# Config
# -------------------------
APP_PORT = int(os.getenv("PORT", "5175"))
DB_PATH  = "./data/airline.sqlite"   # Database file path

app = Flask(__name__, static_folder="web", static_url_path="")

# -------------------------
# DB helpers
# -------------------------
def query_db(sql, args=(), one=False):
    """Execute SQL query and return rows as dictionaries."""
    # The database file must be in the 'data' folder at the same level as server.py
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows

# -------------------------
# Serve front-end 
# -------------------------
@app.route("/")
def serve_index():
    return send_from_directory("web", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("web", path)

# -------------------------
# APIs 
# -------------------------
@app.route("/api/health")
def health():
    """Simple health check for server and database."""
    return jsonify({"ok": os.path.exists(DB_PATH)})

@app.route("/api/employees")
def employees():
    """
    List employees for UI (checkbox list).
    Returns: [{eid, ename}], where ename = fname + ' ' + lname.
    Sorted by eid ASC.
    """
    rows = query_db("""
        SELECT eid, fname || ' ' || lname AS ename
        FROM Employee
        ORDER BY eid ASC
    """)
    return jsonify({"data": [dict(r) for r in rows]})

@app.route("/api/flights-per-aircraft")
def flights_per_aircraft():
    """
    Bar chart data: flights per aircraft (labels = mname + ' ' + model).
    Two modes:
      (A) No ?eids parameter -> return all flights per aircraft.
      (B) ?eids=E1,E2,E3 -> return flights per aircraft filtered by selected employees.
    """
    eids_param = request.args.get("eids")
    if not eids_param:
        single = request.args.get("eid", type=int)
        if single is not None:
            eids_param = str(single)

    # (A) Overall mode
    if not eids_param:
        rows = query_db("""
            SELECT a.aid,
                   a.mname || ' ' || a.model AS label,
                   COUNT(f.flno) AS flights
            FROM Aircraft a
            JOIN Flight f ON f.aid = a.aid
            GROUP BY a.aid
            ORDER BY flights DESC, a.aid ASC
        """)
        data = [{"aid": r["aid"], "label": r["label"], "flights": int(r["flights"])} for r in rows]
        return jsonify({"data": data})

    # (B) Employee filter mode
    eids = [e.strip() for e in eids_param.split(",") if e.strip()]
    eids = list(dict.fromkeys(eids))[:3]

    def get_name(eid):
        r = query_db("""
            SELECT fname || ' ' || lname AS ename
            FROM Employee
            WHERE eid = ?
        """, (eid,), one=True)
        return r["ename"] if r else str(eid)

    by_emp = {}
    aircraft_labels = {}

    for eid in eids:
        rows = query_db("""
            SELECT a.aid,
                   a.mname || ' ' || a.model AS label,
                   COUNT(f.flno) AS flights
            FROM Aircraft a
            JOIN Flight f ON f.aid = a.aid
            WHERE a.aid IN (SELECT c.aid FROM Certificate c WHERE c.eid = ?)
            GROUP BY a.aid
            ORDER BY a.aid ASC
        """, (eid,))
        inner = {}
        for r in rows:
            inner[r["aid"]] = int(r["flights"])
            aircraft_labels[r["aid"]] = r["label"]
        by_emp[eid] = inner

    if not aircraft_labels:
        return jsonify({"labels": [], "series": [{"eid": int(e), "ename": get_name(e), "counts": []} for e in eids]})

    sorted_pairs = sorted(aircraft_labels.items(), key=lambda x: x[1].lower())
    aids   = [aid for aid, _ in sorted_pairs]
    labels = [lbl for _, lbl in sorted_pairs]

    series = []
    for eid in eids:
        counts = [by_emp.get(eid, {}).get(aid, 0) for aid in aids]
        series.append({"eid": int(eid), "ename": get_name(eid), "counts": counts})

    return jsonify({"labels": labels, "series": series})

@app.route("/api/employee-salary-cert")
def employee_salary_cert():
    """
    Right table: employees with at least one certificate.
    Columns: eid (for checkbox), ename, salary, cert_count.
    Sorted by salary DESC.
    """
    rows = query_db("""
        SELECT
            e.eid,
            e.fname || ' ' || e.lname AS ename,
            e.salary,
            COUNT(c.aid) AS cert_count
        FROM Employee e
        JOIN Certificate c ON c.eid = e.eid
        GROUP BY e.eid
        HAVING COUNT(c.aid) > 0
        ORDER BY e.salary DESC
    """)
    return jsonify({"data": [dict(r) for r in rows]})

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
