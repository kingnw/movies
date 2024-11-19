import unittest  # Importing the Python unit testing framework
from app import app, db  # Import the Flask app and the database object from your project
from models import User, UserMovies  # Import the User and UserMovies models
from unittest.mock import patch  # Import the patch utility to mock API calls

class AppTestCase(unittest.TestCase):
    # This is a test class for our Flask app.

    def setUp(self):
        """Set up the test environment."""
        # This method runs before each test.
        # We configure the app for testing and create an in-memory database.

        self.app = app  # Use the app from the project
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for testing
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable SQLAlchemy tracking to save resources
        self.app.testing = True  # Set the app in testing mode
        self.client = self.app.test_client()  # Create a test client for simulating HTTP requests

        # Create the database tables and add a test user
        with self.app.app_context():  # Ensure we're working inside the app context
            db.create_all()  # Create all tables
            user = User(username='testuser', password='testpassword')  # Create a test user
            db.session.add(user)  # Add the user to the database
            db.session.commit()  # Save the user to the database

    def tearDown(self):
        """Clean up after each test."""
        # This method runs after each test to clean up the database.

        with self.app.app_context():  # Inside the app context
            db.session.remove()  # Remove the database session
            db.drop_all()  # Drop all tables to reset the database

    def login_test_user(self):
        """Helper method to log in the test user."""
        # This method logs in the test user by sending a POST request to the login route.
        
        return self.client.post('/auth/login', data={
            'username': 'testuser',  # The username of the test user
            'password': 'testpassword'  # The password of the test user
        }, follow_redirects=True)  # Follow any redirects automatically

    def test_filter_watchlist(self):
        """Test filtering the watchlist."""
        # This test checks if the filter functionality works for the watchlist.

        self.login_test_user()  # Log in the test user so we can access the watchlist

        # Add a test movie to the user's watchlist
        with self.app.app_context():  # Inside the app context
            user = User.get('testuser')  # Get the test user from the database
            movie = UserMovies(user_id=user.id, movie_id=1, category='watchlist')  # Create a test movie
            db.session.add(movie)  # Add the movie to the database
            db.session.commit()  # Save changes

        # Simulate a GET request to filter the watchlist by rating (high to low)
        response = self.client.get('/filter_watchlist?sortby=rating_desc', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)
        self.assertIn(b"Your Watchlist", response.data)  # Check if "Your Watchlist" is in the response HTML

    def test_search_movie(self):
        """Test the search bar functionality."""
        # This test checks if the search bar returns results for a movie title.

        # Simulate a POST request to search for "Inception"
        response = self.client.post('/recommend', data={"movie_title": "Inception"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)
        self.assertIn(b"Inception", response.data)  # Check if "Inception" is in the response HTML

    @patch('app.requests.get')  # Mock the requests.get function
    def test_api_fetching(self, mock_get):
        """Test API fetching with mocked response."""
        # This test checks if the app handles API data correctly by mocking the API response.

        # Mock the API response for top-rated movies
        mock_get.return_value.status_code = 200  # Simulate a 200 OK response
        mock_get.return_value.json.return_value = {
            "results": [{"id": 1, "title": "Mock Movie", "vote_average": 8.5, "poster_path": None}]
            # Simulate a list of movies with one movie
        }

        # Mock the get_languages() function, which fetches supported languages
        with patch('app.get_languages', return_value=[{"code": "en", "name": "English"}]):
            # Simulate a GET request to the top-rated movies page
            response = self.client.get('/top-rated')
            self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)
            self.assertIn(b"Mock Movie", response.data)  # Check if "Mock Movie" is in the response HTML


if __name__ == '__main__':
    unittest.main()  # Run the tests when the script is executed
