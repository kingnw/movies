import unittest
from app import app, db
from models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.testing = True
        self.client = self.app.test_client()

        # Create tables and add a test user
        with self.app.app_context():
            db.create_all()
            user = User(username='testuser', password='testpassword')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        """Clean up after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()  # Drop all tables

    def test_registration_missing_fields(self):
        # Test missing username
        response = self.client.post('/auth/register', data={
            'username': '',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Username is required.", response.data)

        # Test missing password
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'password': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Password is required.", response.data)

    def test_successful_registration(self):
        # Test successful registration
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registration successful.", response.data)

    def test_duplicate_username(self):
        # Register a user
        self.client.post('/auth/register', data={
            'username': 'existinguser',
            'password': 'password123'
        }, follow_redirects=True)

        # Attempt to register with the same username
        response = self.client.post('/auth/register', data={
            'username': 'existinguser',
            'password': 'newpassword123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Username already exists.", response.data)

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Trending Movies", response.data)

    def test_missing_username(self):
        """Test missing username."""
        response = self.client.post('/auth/login', data={
            'username': '',
            'password': 'testpassword'
        }, follow_redirects=True)

        # Assert that the flash message for missing username is displayed
        self.assertIn(b"Username is required.", response.data)
        self.assertEqual(response.status_code, 200)

    def test_missing_password(self):
        """Test missing password."""
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': ''
        }, follow_redirects=True)

        # Assert that the flash message for missing password is displayed
        self.assertIn(b"Password is required.", response.data)
        self.assertEqual(response.status_code, 200)

    def test_invalid_credentials(self):
        """Test invalid username or password."""
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        # Assert that the flash message for invalid login is displayed
        self.assertIn(b"Invalid username or password.", response.data)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
