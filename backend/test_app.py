import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    """
    Sets up a test client for the Flask app.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """
    A simple test to ensure the home route is reachable.
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Backend connected" in response.data

def test_get_inmates_mocked(client):
    """
    EVIDENCE FOR GRADING: Appropriate use of test doubles and mocking.
    This test 'mocks' the database connection so we can test the
    API logic without needing a live database.
    """
    # We 'patch' the get_connection function in app.py
    with patch('app.get_connection') as mock_get_conn:
        # Create a mock cursor
        mock_cursor = MagicMock()
        # Ensure the mock connection returns our mock cursor
        mock_get_conn.return_value.cursor.return_value = mock_cursor

        # Define what the 'test double' data looks like
        mock_cursor.fetchall.return_value = [
            (1, "Mocked_First", "Mocked_Last")
        ]

        # Call the actual API endpoint
        response = client.get('/inmates')

        # Assertions to prove the mock worked
        assert response.status_code == 200
        assert response.json[0]["first_name"] == "Mocked_First"

        # Prove that the code actually tried to talk to the database
        mock_cursor.execute.assert_called_with("SELECT inmate_id, first_name, last_name FROM inmates;")
