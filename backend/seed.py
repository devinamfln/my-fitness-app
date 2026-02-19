import sqlite3

def seed():
    # This creates 'fitness.db' in the same folder as seed.py
    db_path = 'fitness.db'

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("Checking/Creating tables...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prisons (
            prison_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prison_name TEXT NOT NULL,
            location TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inmates (
            inmate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE,
            height_cm FLOAT,
            weight_kg FLOAT,
            prison_id INTEGER,
            FOREIGN KEY (prison_id) REFERENCES prisons(prison_id)
        );
    """)

    # Seed initial data
    cur.execute("SELECT COUNT(*) FROM prisons")
    if cur.fetchone()[0] == 0:
        print("Inserting demo data...")
        cur.execute("INSERT INTO prisons (prison_name, location) VALUES (?, ?)", ("HMP Belmarsh", "London"))
        cur.execute("INSERT INTO inmates (first_name, last_name, date_of_birth, height_cm, weight_kg, prison_id) VALUES (?, ?, ?, ?, ?, ?)",
                    ("John", "Doe", "1990-01-01", 180, 85, 1))
        conn.commit()
        print("Seeding complete.")
    else:
        print("Database already contains data. Skipping seed.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    seed()