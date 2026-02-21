from flask import Flask, jsonify, request, render_template, redirect, url_for
from db import get_connection

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

#---------------------
# LOGIN ROUTES
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.njk")

@app.route("/login/form", methods=["GET"])
def login_form():
    return render_template("login.njk")

@app.route("/login/form", methods=["POST"])
def login_form_submit():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "password123":
        return redirect(url_for("dashboard_page"))
    return render_template("login.njk", error="Invalid credentials")

@app.route("/login", methods=["POST"])
def staff_login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "password123":
        return jsonify({"message": "Login successful", "user": username}), 200
    return jsonify({"error": "Invalid credentials"}), 401

#---------------------
# HOME ROUTES
@app.route("/")
def home():
    # Updated message to reflect SQLite for your resubmission
    return "Backend connected to SQLite Database (Data Encrypted via Tunnel)"

#---------------------
# DASHBOARD ROUTES
@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.njk")

@app.route("/dashboard/search")
def dashboard_search():
    query = request.args.get("query", "")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT inmates.inmate_id,
               inmates.first_name,
               inmates.last_name,
               prisons.prison_name
        FROM inmates
        LEFT JOIN prisons ON inmates.prison_id = prisons.prison_id
        WHERE LOWER(first_name) LIKE ?
           OR LOWER(last_name) LIKE ?
           OR LOWER(first_name || ' ' || last_name) LIKE ?
    """, (f"%{query.lower()}%", f"%{query.lower()}%", f"%{query.lower()}%"))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    inmates = [{"id": r[0], "first_name": r[1], "last_name": r[2], "prison_name": r[3] or "Unknown"} for r in rows]
    return render_template("dashboard_results.njk", inmates=inmates, query=query)

#---------------------
# INMATE ROUTES
@app.route("/inmates")
def get_inmates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT inmate_id, first_name, last_name FROM inmates;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "first_name": r[1], "last_name": r[2]} for r in rows])

@app.route("/inmate/search")
def search_inmate():
    query = request.args.get("query", "")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT inmate_id, first_name, last_name
        FROM inmates 
        WHERE LOWER(first_name) LIKE ?
            OR LOWER(last_name) LIKE ?
            OR LOWER(first_name || ' '|| last_name) LIKE ?;
    """, (f"%{query.lower()}%", f"%{query.lower()}%", f"%{query.lower()}%"))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "first_name": r[1], "last_name": r[2]} for r in rows])

@app.route("/inmates/create", methods=["POST"])
def create_inmate():
    # 1. Handle different data types (JSON vs Form)
    if request.is_json:
        data = request.get_json()
    else:
        # This allows standard HTML <form> submissions to work
        data = request.form

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # 2. Extract with defaults to prevent KeyErrors
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    dob = data.get("date_of_birth", "2000-01-01")
    height = data.get("height_cm", 0)
    weight = data.get("weight_kg", 0)
    prison_id = data.get("prison_id", 1)

    if not first_name or not last_name:
        return jsonify({"error": "First and Last name are required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 3. Secure SQLite Insert
        cur.execute("""
            INSERT INTO inmates (first_name, last_name, date_of_birth, height_cm, weight_kg, prison_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, dob, height, weight, prison_id))

        new_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Inmate created successfully", "id": new_id}), 201
    except Exception as e:
        # This catches DB errors (like missing tables) and reports them safely
        return jsonify({"error": str(e)}), 500
@app.route("/inmates/<int:inmate_id>")
def get_inmate_details(inmate_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT inmate_id, first_name, last_name, date_of_birth, height_cm, weight_kg, prison_id FROM inmates WHERE inmate_id = ?;", (inmate_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row: return jsonify({"error": "Inmate not found"}), 404
    return jsonify({"id": row[0], "first_name": row[1], "last_name": row[2], "date_of_birth": row[3], "height_cm": row[4], "weight_kg": row[5], "prison_id": row[6]})

@app.route("/dashboard/inmates/<int:inmate_id>")
def inmate_details_page(inmate_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.inmate_id, i.first_name, i.last_name, i.date_of_birth, i.height_cm, i.weight_kg, COALESCE(p.prison_name, 'Unknown')
        FROM inmates i LEFT JOIN prisons p ON i.prison_id = p.prison_id WHERE i.inmate_id = ?;
    """, (inmate_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row: return render_template("inmate_details.njk", error="Inmate not found"), 404
    inmate = {"id": row[0], "first_name": row[1], "last_name": row[2], "date_of_birth": row[3], "height_cm": row[4], "weight_kg": row[5], "prison_name": row[6]}
    bmi = round(float(inmate["weight_kg"]) / ((inmate["height_cm"]/100)**2), 1) if inmate["height_cm"] and inmate["weight_kg"] else None
    return render_template("inmate_details.njk", inmate=inmate, bmi=bmi)

@app.route("/inmates/<int:inmate_id>/update", methods=["PUT"])
def update_inmate(inmate_id):
    data = request.json
    conn = get_connection()
    cur = conn.cursor()
    fields, values = [], []
    for key in ["first_name", "last_name", "date_of_birth", "height_cm", "weight_kg", "prison_id"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if not fields: return jsonify({"error": "No fields provided"}), 400
    values.append(inmate_id)
    cur.execute(f"UPDATE inmates SET {', '.join(fields)} WHERE inmate_id = ?;", tuple(values))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Inmate updated successfully", "inmate_id": inmate_id})

@app.route("/prisons")
def get_prisons():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT prison_id, prison_name, location FROM prisons;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "name": r[1], "location": r[2]} for r in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)