from unittest.mock import patch
import pytest
from db import get_connection

try:
    conn = get_connection()
    print("connected successfully")
    conn.close()
except Exception as e:
    print("Error",e)


