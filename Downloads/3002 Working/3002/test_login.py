import unittest  # Import the unittest framework
from app import app, db  # Import the Flask app and the database object
from models import User  # Import the User model

class AuthTestCase(unittest.TestCase):
    # This is a test class to verify the functionality of user authentication.

    def setUp(self):
        """Set up the test environment."""
        # This method runs before every test to set up the environment.

        self.app = app  # Use the app instance from the project
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for isolated testing
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable SQLAlchemy tracking to save resources
        self.app.testing = True  # Enable testing mode for Flask
        self.client = self.app.test_client()  # Create a test client for simulating HTTP requests

        # Create database tables and add a test user
        with self.app.app_context():  # Ensure we're in the app context
            db.create_all()  # Create all database tables
            user = User(username='testuser', password='testpassword')  # Create a test user
            db.session.add(user)  # Add the user to the database
            db.session.commit()  # Save the user in the database

    def tearDown(self):
        """Clean up after each test."""
        # This method runs after every test to clean up the database.

        with self.app.app_context():  # Inside the app context
            db.session.remove()  # Remove the database session
            db.drop_all()  # Drop all database tables

    def test_registration_missing_fields(self):
        """Test registration with missing fields."""
        # Test missing username
        response = self.client.post('/auth/register', data={
            'username': '',  # No username provided
            'password': 'password123'  # Valid password
        }, follow_redirects=True)  # Follow any redirects
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)
        self.assertIn(b"Username is required.", response.data)  # Check for the error message in the response

        # Test missing password
        response = self.client.post('/auth/register', data={
            'username': 'testuser',  # Valid username
            'password': ''  # No password provided
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)
        self.assertIn(b"Password is required.", response.data)  # Check for the error message in the response

    def test_successful_registration(self):
        """Test successful registration."""
        response = self.client.post('/auth/register', data={
            'username': 'newuser',  # New username
            'password': 'password123'  # Valid password
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)
        self.assertIn(b"Registration successful.", response.data)  # Check for the success message in the response

    def test_duplicate_username(self):
        """Test registration with a duplicate username."""
        # Register a user with a username
        self.client.post('/auth/register', data={
            'username': 'existinguser',  # Username that already exists
            'password': 'password123'  # Valid password
        }, follow_redirects=True)

        # Attempt to register with the same username
        response = self.client.post('/auth/register', data={
            'username': 'existinguser',  # Same username
            'password': 'newpassword123'  # Different password
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)
        self.assertIn(b"Username already exists.", response.data)  # Check for the error message

    def test_index_page(self):
        """Test accessing the home page."""
        response = self.client.get('/')  # Simulate a GET request to the home page
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)
        self.assertIn(b"Trending Movies", response.data)  # Check for "Trending Movies" in the response

    def test_missing_username(self):
        """Test login with a missing username."""
        response = self.client.post('/auth/login', data={
            'username': '',  # No username provided
            'password': 'testpassword'  # Valid password
        }, follow_redirects=True)
        self.assertIn(b"Username is required.", response.data)  # Check for the error message
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)

    def test_missing_password(self):
        """Test login with a missing password."""
        response = self.client.post('/auth/login', data={
            'username': 'testuser',  # Valid username
            'password': ''  # No password provided
        }, follow_redirects=True)
        self.assertIn(b"Password is required.", response.data)  # Check for the error message
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)

    def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/auth/login', data={
            'username': 'testuser',  # Valid username
            'password': 'wrongpassword'  # Incorrect password
        }, follow_redirects=True)
        self.assertIn(b"Invalid username or password.", response.data)  # Check for the error message
        self.assertEqual(response.status_code, 200)  # Check that the status code is 200 (OK)


if __name__ == '__main__':
    unittest.main()  # Run the tests when the script is executed
