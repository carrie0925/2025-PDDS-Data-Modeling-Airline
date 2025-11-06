from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os

# -------------------------
# Config
# -------------------------
APP_PORT = int(os.getenv("PORT", "5175"))
DB_PATH  = "./data/airline.sqlite"   # <- simple sqlite3 path (teaching-friendly)

app = Flask(__name__, static_folder="web", static_url_path="")

# -------------------------
# DB helpers
# -------------------------
def query_db(sql, args=(), one=False):
    """Execute a read-only query and return rows as dict-like objects."""
    conn = sqlite3.connect(DB_PATH)     # <- sqlite3.connect('...') style
    conn.row_factory = sqlite3.Row
    cur = conn.execute(sql, args)
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
# APIs (no debug endpoints)
# -------------------------
@app.route("/api/health")
def health():
    """Simple liveness & DB presence check."""
    return jsonify({"ok": os.path.exists(DB_PATH)})

@app.route("/api/employees")
def employees():
    """
    # TODO 01:
    Goal: Retrieve the list of employees for the front-end checkbox menu.
    Expected result: Each record represents one employee.
    Required columns:
        - eid
        - ename  (combine first and last name into one readable field)
    Sorting:
        - Order results by eid in ascending order.
    """
    rows = query_db("""
        -- WRITE YOUR SQL HERE
    """)
    return jsonify({"data": [dict(r) for r in rows]})

@app.route("/api/flights-per-aircraft")
def flights_per_aircraft():
    """
    Generate bar chart data for flights per aircraft.

    Two modes:
      - Without eids: all aircraft with total flight counts
      - With ?eids=E1,E2,E3: compare multiple employees' certified aircraft
    """
    eids_param = request.args.get("eids")
    if not eids_param:
        single = request.args.get("eid", type=int)
        if single is not None:
            eids_param = str(single)

    # without eids: overall flights per aircraft
    if not eids_param:
        """
        # TODO 02:
        Goal: Calculate how many flights exist for each aircraft across the entire fleet.
        Expected result: One row per aircraft with the total flight count.
        Required columns:
            - aid
            - label  (combine mname and model to describe aircraft)
            - flights  (use an aggregate count of all flights)
        Relationships & grouping:
            - Must connect aircraft information with flight records.
            - Aggregate results by aircraft identifier.
        Sorting:
            - Sort first by flight count from highest to lowest, 
              then by aircraft ID in ascending order.
        """
        rows = query_db("""
            -- WRITE YOUR SQL HERE
        """)
        data = [{"aid": r["aid"], "label": r["label"], "flights": int(r["flights"])} for r in rows]
        return jsonify({"data": data})

    # with eids: compare multiple employees (max 3)
    eids = [e.strip() for e in eids_param.split(",") if e.strip()]
    eids = list(dict.fromkeys(eids))[:3]

    def get_name(eid):
        """
        # TODO 03:
        Goal: Retrieve the full name of a specific employee using their employee ID.
        Expected result: One record containing only that employee’s name.
        Required columns:
            - ename  (combine first and last name into a single alias)
        Filtering:
            - Return only the employee whose ID matches the given parameter.
        """
        r = query_db("""
            -- WRITE YOUR SQL HERE
        """, (eid,), one=True)
        return r["ename"] if r and "ename" in r.keys() else str(eid)

    by_emp = {}          # eid -> {aid: flights}
    aircraft_labels = {} # aid -> "mname model"

    for eid in eids:
        """
        # TODO 04:
        Goal: Find all aircraft that one selected employee is certified to operate,
              along with the number of flights for each of those aircraft.
        Expected result: Multiple rows, one per aircraft, showing flight frequency.
        Required columns:
            - aid
            - label  (combine mname and model to describe aircraft)
            - flights  (total number of flights on that aircraft)
        Relationships & filtering:
            - Use aircraft and flight data, but include only aircraft linked
              to that employee’s certifications.
            - The filtering should depend on the employee’s ID.
        Grouping & sorting:
            - Summarize by aircraft ID.
            - Present results in ascending order of aircraft ID.
        """
        rows = query_db("""
            -- WRITE YOUR SQL HERE
        """, (eid,))
        inner = {}
        for r in rows:
            inner[r["aid"]] = int(r["flights"])
            aircraft_labels[r["aid"]] = r["label"]
        by_emp[eid] = inner

    if not aircraft_labels:
        return jsonify({"labels": [], "series": [{"eid": int(e), "ename": get_name(e), "counts": []} for e in eids]})

    # Stable x-axis: sort alphabetically by label
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
    # TODO 05:
    Goal: List employees who possess at least one valid aircraft certificate.
    Expected result: Each row shows one employee with their salary
                     and the number of certificates they hold.
    Required columns:
        - eid
        - ename  (combine first and last name)
        - salary
        - cert_count  (count total certificates for each employee)
    Relationships & grouping:
        - Combine employee data with certificate information.
        - Include only employees whose certificate count is greater than zero.
    Sorting:
        - Display employees in order of salary, from highest to lowest.
    """
    rows = query_db("""
        -- WRITE YOUR SQL HERE
    """)
    return jsonify({"data": [dict(r) for r in rows]})

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
