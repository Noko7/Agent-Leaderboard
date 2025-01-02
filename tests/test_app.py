import unittest
from app import app
import os
import sqlite3
import uuid

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Set up a clean test database and test client."""
        self.TEST_DB = f"test_database_{uuid.uuid4().hex}.db"  # Unique DB file for each test
        app.config['TESTING'] = True
        app.config['DATABASE'] = self.TEST_DB
        self.app = app.test_client()

        # Initialize a clean test database
        self.initialize_test_database()

    def tearDown(self):
        """Clean up the test database after each test."""
        try:
            conn = sqlite3.connect(self.TEST_DB)
            conn.close()  # Ensure all connections are closed
        except sqlite3.Error as e:
            print(f"Error closing test database connection: {str(e)}")

        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)

    def initialize_test_database(self):
        """Initialize the test database with required tables."""
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()

        # Drop existing tables if they exist
        cursor.execute('DROP TABLE IF EXISTS agents')
        cursor.execute('DROP TABLE IF EXISTS transactions')

        # Create agents table
        cursor.execute('''
            CREATE TABLE agents (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # Create transactions table
        cursor.execute('''
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                agent_id INTEGER,
                volume REAL,
                date TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        ''')

        # Seed initial data
        cursor.executemany('INSERT INTO agents (name) VALUES (?)', [('Alice',), ('Bob',)])
        conn.commit()
        conn.close()

    def get_test_database_connection(self):
        """Get a connection to the test database."""
        return sqlite3.connect(self.TEST_DB)

    def print_test_database_state(self):
        """Print the current state of the test database for debugging."""
        conn = self.get_test_database_connection()
        cursor = conn.cursor()

        # Print agents
        print("\n=== Agents Table ===")
        agents = cursor.execute('SELECT * FROM agents').fetchall()
        for agent in agents:
            print(agent)

        # Print transactions
        print("\n=== Transactions Table ===")
        transactions = cursor.execute('SELECT * FROM transactions').fetchall()
        for transaction in transactions:
            print(transaction)

        conn.close()
