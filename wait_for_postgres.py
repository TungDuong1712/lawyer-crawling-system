#!/usr/bin/env python3
"""
Wait for PostgreSQL to be ready before starting the application.
"""
import sys
import time
import psycopg2
from psycopg2 import OperationalError


def wait_for_postgres(host='db', port=5432, user='crawler', password='password', database='lawyers_db', max_retries=30, delay=2):
    """
    Wait for PostgreSQL to be ready.
    
    Args:
        host: PostgreSQL host
        port: PostgreSQL port
        user: PostgreSQL user
        password: PostgreSQL password
        database: Database name
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    print(f"Waiting for PostgreSQL at {host}:{port}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.close()
            print(f"PostgreSQL is ready!")
            return True
        except OperationalError as e:
            if attempt < max_retries:
                print(f"Attempt {attempt}/{max_retries}: PostgreSQL is not ready yet. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Error: Could not connect to PostgreSQL after {max_retries} attempts.")
                print(f"Error details: {e}")
                return False
    
    return False


if __name__ == '__main__':
    # Get connection details from environment variables or use defaults
    import os
    
    host = os.getenv('DB_HOST', 'db')
    port = int(os.getenv('DB_PORT', '5432'))
    user = os.getenv('DB_USER', 'crawler')
    password = os.getenv('DB_PASSWORD', 'password')
    database = os.getenv('DB_NAME', 'lawyers_db')
    
    success = wait_for_postgres(host=host, port=port, user=user, password=password, database=database)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)

