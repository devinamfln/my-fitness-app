import sqlite3

def get_connection():
    """
    Creates a connection to a local SQLite database.
    In production, you would swap this for PostgreSQL or MySQL logic.
    """
    try:
        # This creates a local file 'fitness.db' if it doesn't exist
        conn = sqlite3.connect('fitness.db')
        return conn
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

if __name__ == "__main__":
    # This block only runs if you execute 'python db.py' directly
    try:
        connection = get_connection()
        if connection:
            print("Connected successfully")
            connection.close()
        else:
            print("Connection returned None")
    except Exception as e:
        print("Error during test run:", e)