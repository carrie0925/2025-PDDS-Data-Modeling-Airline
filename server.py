from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os, traceback

# ======================
# 基本設定
# ======================
APP_PORT = int(os.getenv("PORT", "5175"))
DB_PATH  = os.getenv("DB_PATH", "./data/airline.sqlite")  # 可改成 .db 或你的實際檔名

app = Flask(__name__, static_folder="web", static_url_path="")

# ======================
# 工具函式
# ======================
def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def query_db(sql, args=(), one=False):
    con = connect()
    try:
        cur = con.execute(sql, args)
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        con.close()

def table_exists(table_name: str) -> bool:
    row = query_db(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND lower(name)=lower(?)",
        (table_name,),
        one=True
    )
    return row is not None

def find_first_table(candidates):
    for name in candidates:
        if table_exists(name):
            return name
    return None

def fail(msg, status=500, detail=None):
    out = {"error": msg}
    if detail:
        out["detail"] = detail
    return jsonify(out), status

# ======================
# Frontend
# ======================
@app.route("/")
def serve_index():
    return send_from_directory("web", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("web", path)

# ======================
# API
# ======================
@app.route("/api/health")
def health():
    ok = os.path.exists(DB_PATH)
    return jsonify({"ok": ok, "db_path": DB_PATH})

@app.route("/api/employees")
def employees():
    try:
        employee_table = find_first_table(["Employee", "Employees"])
        if not employee_table:
            return fail("找不到 Employee 表", 404)
        rows = query_db(f"""
            SELECT eid, fname || ' ' || lname AS ename
            FROM {employee_table}
            ORDER BY eid ASC
        """)
        return jsonify({"data": [dict(r) for r in rows]})
    except Exception as e:
        traceback.print_exc()
        return fail("employees query failed", 500, detail=str(e))

@app.route("/api/flights-per-aircraft")
def flights_per_aircraft():
    """
    支援：
    - 無參數：回傳整體 flights per aircraft（單一 dataset）
    - ?eids=1,2,3：回傳多名員工比較（多 dataset）
    labels 僅為 mname + model；y 軸為整數 flight count
    """
    try:
        aircraft_table   = find_first_table(["Aircraft"])
        flight_table     = find_first_table(["Flight"])
        certificate_tbl  = find_first_table(["Certificate"])
        employee_table   = find_first_table(["Employee", "Employees"])

        if not aircraft_table or not flight_table:
            return fail("找不到 Aircraft 或 Flight 表", 404)

        eids_param = request.args.get("eids")
        if not eids_param:
            single = request.args.get("eid", type=int)
            if single is not None:
                eids_param = str(single)

        # --- 無 eids：整體 ---
        if not eids_param:
            sql = f"""
            SELECT a.aid,
                   a.mname || ' ' || a.model AS label,
                   COUNT(f.flno) AS flights
            FROM {aircraft_table} a
            JOIN {flight_table} f ON f.aid = a.aid
            GROUP BY a.aid
            ORDER BY flights DESC, a.aid ASC
            """
            rows = query_db(sql)
            data = [{"aid": r["aid"], "label": r["label"], "flights": int(r["flights"])} for r in rows]
            return jsonify({"data": data})

        # --- 多選 eids：比較 ---
        if not certificate_tbl or not employee_table:
            return jsonify({"labels": [], "series": []})

        eids = [e.strip() for e in eids_param.split(",") if e.strip()]
        eids = list(dict.fromkeys(eids))[:3]  # 最多 3 人

        def get_name(eid):
            row = query_db(f"SELECT fname || ' ' || lname AS ename FROM {employee_table} WHERE eid = ?", (eid,), one=True)
            return row["ename"] if row else str(eid)

        by_emp = {}          # eid -> { aid: flights }
        aircraft_labels = {} # aid -> "mname model"

        for eid in eids:
            rows = query_db(f"""
                SELECT a.aid,
                       a.mname || ' ' || a.model AS label,
                       COUNT(f.flno) AS flights
                FROM {aircraft_table} a
                JOIN {flight_table}   f ON f.aid = a.aid
                WHERE a.aid IN (SELECT c.aid FROM {certificate_tbl} c WHERE c.eid = ?)
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

    except Exception as e:
        traceback.print_exc()
        return fail("flights-per-aircraft query failed", 500, detail=str(e))

@app.route("/api/employee-salary-cert")
def employee_salary_cert():
    """
    表格資料：
    - 不顯示 eid，但仍在 JSON 中保留給 checkbox 使用
    - 僅列出有證照的員工（HAVING COUNT>0）
    - 依 salary DESC 排序
    """
    try:
        employee_table   = find_first_table(["Employee", "Employees"])
        certificate_tbl  = find_first_table(["Certificate"])

        if not employee_table:
            return fail("找不到 Employee 表", 404)
        if not certificate_tbl:
            return jsonify({"data": []})

        sql = f"""
        SELECT
            e.eid,
            e.fname || ' ' || e.lname AS ename,
            e.salary,
            COUNT(c.aid) AS cert_count
        FROM {employee_table} e
        JOIN {certificate_tbl} c ON c.eid = e.eid
        GROUP BY e.eid
        HAVING COUNT(c.aid) > 0
        ORDER BY e.salary DESC
        """
        rows = query_db(sql)
        return jsonify({"data": [dict(r) for r in rows]})
    except Exception as e:
        traceback.print_exc()
        return fail("employee-salary-cert query failed", 500, detail=str(e))

# ======================
# 執行
# ======================
if __name__ == "__main__":
    print(f"[INFO] Using DB at: {DB_PATH} ({'found' if os.path.exists(DB_PATH) else 'NOT found'})")
    app.run(host="0.0.0.0", port=APP_PORT, debug=True)
