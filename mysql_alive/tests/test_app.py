import os
import pytest
import requests
import time
import mysql.connector
from mysql.connector import Error

# Function to check if MySQL is accessible
def is_mysql_alive():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_user = os.getenv('DB_USER', 'root')  # Get user from environment variable
    db_password = os.getenv('DB_PASSWORD', '123456')  # Get password from environment variable

    try:
        # Try connecting to MySQL database
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        if connection.is_connected():
            connection.close()
            return True
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return False

    return False

# Test case to check if MySQL database is alive and Flask endpoint is working
@pytest.mark.parametrize("db_host, db_port", [
    ('localhost', '3306'),
    # You can add other host and port pairs as needed for testing
])
def test_is_db_alive(db_host, db_port):
    SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
    SERVER_PORT = os.getenv('SERVER_PORT', '5000')
    # Retry to connect to the MySQL service with exponential backoff
    max_retries = 5
    base_delay = 1  # 1 second initial delay
    for attempt in range(max_retries):
        if is_mysql_alive():
            break
        else:
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            print(f"Attempt {attempt+1} failed to connect to MySQL, retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        pytest.fail("Failed to connect to MySQL database after several attempts.")

    # Test the actual Flask endpoint
    response = requests.get(f'http://{SERVER_HOST}:{SERVER_PORT}/is-db-alive')

    # Assert that the response is successful (HTTP status code 200)
    assert response.status_code == 200
    assert 'DB is alive' in response.text
