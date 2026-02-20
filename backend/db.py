import sqlite3
import os

def get_connection():
    """
    Creates a connection to a local SQLite database using an absolute path.
    This ensures Gunicorn and Seed.py always look at the same file.
    """
    # Define exactly where the database should live on the EC2
    base_dir = "/home/ec2-user/my-fitness-app/backend"
    db_path = os.path.join(base_dir, "fitness.db")

    # If running locally (not on EC2), fall back to the local folder
    if not os.path.exists(base_dir):
        db_path = os.path.join(os.path.dirname(__file__), 'fitness.db')

    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

if __name__ == "__main__":
    connection = get_connection()
    if connection:
        print(f"Connected successfully to: {connection}")
        connection.close()