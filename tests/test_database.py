from tests.test_app import BaseTestCase
import sqlite3

class TestDatabase(BaseTestCase):
    def test_add_agent(self):
        """Test adding an agent to the database."""
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()

        # Add an agent
        cursor.execute('INSERT INTO agents (name) VALUES (?)', ('Alice',))
        conn.commit()

        # Verify agent was added
        cursor.execute('SELECT * FROM agents WHERE name = ?', ('Alice',))
        agent = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(agent, "Failed to add agent 'Alice' to the database.")
        self.assertEqual(agent[1], 'Alice', "Agent name mismatch in the database.")

    def test_add_transaction(self):
        """Test adding a transaction to the database."""
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()

        # Add an agent
        cursor.execute('INSERT INTO agents (name) VALUES (?)', ('Bob',))
        agent_id = cursor.lastrowid

        # Add a transaction
        cursor.execute('INSERT INTO transactions (agent_id, volume, date) VALUES (?, ?, ?)',
                       (agent_id, 1000.50, '2024-12-28'))
        conn.commit()

        # Verify transaction was added
        cursor.execute('SELECT * FROM transactions WHERE agent_id = ?', (agent_id,))
        transaction = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(transaction, "Failed to add transaction to the database.")
        self.assertEqual(transaction[1], agent_id, "Agent ID mismatch in the transaction.")
        self.assertAlmostEqual(transaction[2], 1000.50, places=2, msg="Transaction volume mismatch.")
