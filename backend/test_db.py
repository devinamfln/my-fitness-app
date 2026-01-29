import pytest
from db import get_connection

def test_database_connection():
    try:
        conn = get_connection()
        assert conn is not None
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")


