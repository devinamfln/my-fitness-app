from flask import Flask, jsonify, request, render_template
from db import get_connection

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.njk")
#adding login


@app.route("/")
def home():
    return "Backend connected to AWS PostgreSQL"

@app.route("/inmates")
def get_inmates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT inmate_id, first_name, last_name FROM inmates;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "first_name": r[1], "last_name": r[2]}
        for r in rows

    ])


# inmate search API
@app.route("/inmate/search")
def search_inmate():
    query = request.args.get("query", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT inmate_id, first_name, last_name
        FROM inmates 
        WHERE LOWER(first_name) LIKE %s
            OR LOWER(last_name) LIKE %s
            OR LOWER(first_name || ' '|| last_name) LIKE %s;
    
    """, (
        f"%{query.lower()}%",
        f"%{query.lower()}%",
        f"%{query.lower()}%"
    ))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "first_name": r[1], "last_name": r[2]}
        for r in rows
    ])


@app.route("/prisons")
def get_prisons():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT prison_id, prison_name, location FROM prisons;")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify ([
        {"id": r[0], "name": r[1], "location": r[2]}
        for r in rows
    ])

@app.route("/inmates/create", methods=["POST"])
def create_inmate():
    data = request.json # Read JSON from POST body

    # Extract values
    first_name= data.get("first_name")
    last_name= data.get("last_name")
    date_of_birth= data.get("date_of_birth")
    height_cm = data.get("height_cm")
    weight_kg = data.get("weight_kg")
    prison_id = data.get("prison_id")

    # Validate required fields
    if not first_name or not last_name or not date_of_birth or not prison_id:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inmates (first_name, last_name, date_of_birth, height_cm, weight_kg, prison_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING inmate_id;
    """, (first_name, last_name, date_of_birth, height_cm, weight_kg, prison_id))

    new_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Inmate created successfully",
        "inmate_id": new_id
    }), 201


@app.route("/inmates/<int:inmate_id>")
def get_inmate_details(inmate_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT inmate_id, first_name, last_name, date_of_birth, height_cm, weight_kg, prison_id
    FROM inmates
    WHERE inmate_id = %s;
    """, (inmate_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Inmate not found"}),404

    return jsonify({
        "id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "date_of_birth": row[3],
        "height_cm": row[4],
        "weight_kg": row[5],
        "prison_id": row[6]
    })


@app.route("/inmates/<int:inmate_id>/update", methods=["PUT"])
def update_inmate(inmate_id):
    data = request.json  # Incoming JSON

    # Connect to DB
    conn = get_connection()
    cur = conn.cursor()

    # Build dynamic update fields
    fields = []
    values = []

    for key in ["first_name", "last_name", "date_of_birth", "height_cm", "weight_kg", "prison_id"]:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        return jsonify({"error": "No fields provided"}), 400

    values.append(inmate_id)

    sql = f"UPDATE inmates SET {', '.join(fields)} WHERE inmate_id = %s RETURNING inmate_id;"

    cur.execute(sql, tuple(values))
    updated = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        return jsonify({"error": 'Inmate not found'}), 404

    return jsonify({"message": "Inmate updated successfully", "inmate_id": inmate_id})



@app.route("/login", methods=["POST"])
def staff_login():
    data = request.json

    username = data.get("username")
    password = data.get("password")

    # Simple demo login (hardcoded)
    if username == "admin" and password == "password123":
        return jsonify({"message": "Login successful", "staff": username}), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/login/form", methods=["GET"])
def login_form():
    return render_template("login.njk")


@app.route("/login/form", methods=["POST"])
def login_form_submit():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "password123":
        return "Login successful (HTML mode)"

    return render_template("login.njk", error="Invalid credentials")







#Always last
if __name__ == "__main__":
    app.run(debug=True)