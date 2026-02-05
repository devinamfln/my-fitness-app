# backend/db.py

def get_connection():
    # Replace this with your actual connection logic (psycopg2, sqlite3, etc.)
    # Example:
    # import sqlite3
    # return sqlite3.connect('fitness.db')
    pass

if __name__ == "__main__":
    try:
        conn = get_connection()
        print("Connected successfully")
        if conn:
            conn.close()
    except Exception as e:
        print("Error:", e)