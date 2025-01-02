from tests.test_app import BaseTestCase


class TestRoutes(BaseTestCase):
    def test_home_page(self):
        """Test that the home page loads correctly."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200, "Home page failed to load.")
        self.assertIn(b'Visualized Data', response.data, "Home page content mismatch.")

    def test_admin_page(self):
        """Test that the admin page loads correctly."""
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 200, "Admin page failed to load.")
        self.assertIn(b'Admin Panel', response.data, "Admin page content mismatch.")

    def test_graphs_route(self):
        """Test the graphs route for the current month."""
        response = self.app.get('/graphs?month=2024-12')
        self.assertEqual(response.status_code, 200, "Graphs route failed to load.")
        self.assertIn('image/png', response.content_type, "Graphs route did not return an image.")

    def test_add_agent(self):
        """Test adding an agent through the admin page."""
        response = self.app.post('/admin', data={'agent_name': 'Charlie', 'add_agent': 'true'}, follow_redirects=True)
        print(f"Debug: Response data for add agent: {response.data.decode('utf-8')}")  # Debugging
        self.assertEqual(response.status_code, 200, "Failed to add agent through admin route.")
        self.assertIn("Agent 'Charlie' added successfully!", response.data.decode('utf-8'), "Add agent message missing.")

    def test_remove_agent(self):
        """Test removing an agent through the admin page."""
        with self.get_test_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO agents (name) VALUES (?)', ('Charlie',))
            agent_id = cursor.lastrowid

        response = self.app.post('/admin', data={'agent_id': agent_id, 'remove_agent': 'true'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200, "Failed to remove agent through admin route.")
        self.assertIn("Agent removed successfully!", response.data.decode('utf-8'), "Remove agent message missing.")

    def test_add_transaction(self):
        """Test adding a transaction through the admin page."""
        with self.get_test_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO agents (name) VALUES (?)', ('Charlie',))
            agent_id = cursor.lastrowid

        response = self.app.post('/admin', data={
            'transaction_agent_id': agent_id,
            'transaction_volume': 1000.50,
            'transaction_date': '2024-12-28',
            'add_transaction': 'true'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200, "Failed to add transaction through admin route.")
        self.assertIn("Transaction added successfully!", response.data.decode('utf-8'), "Add transaction message missing.")

    def test_remove_transaction(self):
        """Test removing a transaction through the admin page."""
        with self.get_test_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO agents (name) VALUES (?)', ('Charlie',))
            agent_id = cursor.lastrowid
            cursor.execute('INSERT INTO transactions (agent_id, volume, date) VALUES (?, ?, ?)', (agent_id, 500.25, '2024-12-28'))
            transaction_id = cursor.lastrowid

        response = self.app.post('/admin', data={'transaction_id': transaction_id, 'remove_transaction': 'true'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200, "Failed to remove transaction through admin route.")
        self.assertIn("Transaction removed successfully!", response.data.decode('utf-8'), "Remove transaction message missing.")
