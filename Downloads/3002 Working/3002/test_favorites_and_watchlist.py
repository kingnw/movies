import unittest  # Import the unittest framework
from app import app, db  # Import the Flask app and the database object
from models import User, UserMovies  # Import the User and UserMovies models


class WatchlistFavoritesTestCase(unittest.TestCase):
    # This test class is for testing the watchlist and favorites functionality.

    def setUp(self):
        """Set up the test environment."""
        # This method runs before every test to prepare the environment.

        self.app = app  # Use the app instance from the project
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for isolated testing
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable SQLAlchemy tracking to save resources
        self.app.testing = True  # Enable testing mode for Flask
        self.client = self.app.test_client()  # Create a test client for simulating HTTP requests

        # Create the database tables and add a test user
        with self.app.app_context():  # Ensure we're working inside the app context
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

    def login_user(self):
        """Helper method to log in a user."""
        # This method logs in the test user by sending a POST request to the login route.
        
        self.client.post('/auth/login', data={
            'username': 'testuser',  # The username of the test user
            'password': 'testpassword'  # The password of the test user
        }, follow_redirects=True)  # Follow any redirects automatically

    def test_add_movie_to_watchlist(self):
        """Test adding a movie to the watchlist."""
        self.login_user()  # Log in the test user
        movie_id = 123  # Example movie ID
        response = self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)  # Add the movie to the watchlist
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)

        # Verify that the movie was added to the watchlist in the database
        with self.app.app_context():
            self.assertIsNotNone(
                UserMovies.query.filter_by(user_id=1, movie_id=movie_id, category='watchlist').first()
            )

    def test_remove_movie_from_watchlist(self):
        """Test removing a movie from the watchlist."""
        self.login_user()  # Log in the test user
        movie_id = 123  # Example movie ID

        # Add a movie to the watchlist first
        self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)

        # Now remove the movie from the watchlist
        response = self.client.post(f'/watchlist/remove/{movie_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)

        # Verify that the movie was removed from the watchlist in the database
        with self.app.app_context():
            self.assertIsNone(
                UserMovies.query.filter_by(user_id=1, movie_id=movie_id, category='watchlist').first()
            )

    def test_view_watchlist(self):
        """Test viewing the watchlist."""
        self.login_user()  # Log in the test user
        movie_id = 123  # Example movie ID

        # Add a movie to the watchlist
        self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)

        # View the watchlist
        response = self.client.get('/watchlist', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)
        self.assertIn(b"Your Watchlist", response.data)  # Check if "Your Watchlist" is in the response HTML

    def test_add_movie_to_favorites(self):
        """Test adding a movie to favorites."""
        self.login_user()  # Log in the test user
        movie_id = 456  # Example movie ID
        response = self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)  # Add the movie to favorites
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)

        # Verify that the movie was added to favorites in the database
        with self.app.app_context():
            self.assertIsNotNone(
                UserMovies.query.filter_by(user_id=1, movie_id=movie_id, category='favorites').first()
            )

    def test_remove_movie_from_favorites(self):
        """Test removing a movie from favorites."""
        self.login_user()  # Log in the test user
        movie_id = 456  # Example movie ID

        # Add a movie to favorites first
        self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)

        # Now remove the movie from favorites
        response = self.client.post(f'/favorites/remove/{movie_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)

        # Verify that the movie was removed from favorites in the database
        with self.app.app_context():
            self.assertIsNone(
                UserMovies.query.filter_by(user_id=1, movie_id=movie_id, category='favorites').first()
            )

    def test_view_favorites(self):
        """Test viewing favorites."""
        self.login_user()  # Log in the test user
        movie_id = 456  # Example movie ID

        # Add a movie to favorites
        self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)

        # View the favorites list
        response = self.client.get('/favorites', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Check that the response status is 200 (OK)
        self.assertIn(b"Your Favorites", response.data)  # Check if "Your Favorites" is in the response HTML


if __name__ == '__main__':
    unittest.main()  # Run the tests when the script is executed
