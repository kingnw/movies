import unittest
from app import app, db  # Ensure you're importing the app with blueprints registered
from models import User, UserMovies
from unittest.mock import patch

class WatchlistFavoritesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        # Configure the app for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

        # Create the test client
        self.client = app.test_client()

        # Create the database and tables
        with app.app_context():
            db.create_all()
            # Create a test user
            self.test_username = "testuser" + str(id(self))
            self.test_password = "testpassword"
            self.user = User(username=self.test_username, password=self.test_password)  # Provide the password
            self.user.set_password(self.test_password)  # Hash the password
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id  # Store the user ID

    def login(self):
        """Helper method to log in the test user."""
        response = self.client.post('/auth/login', data=dict(
            username=self.test_username,
            password=self.test_password
        ), follow_redirects=True)
        
        # Assert that the login was successful by checking for a success message
        self.assertIn(b'Logged in successfully.', response.data)
        self.assertEqual(response.status_code, 200)
        
        # Optionally, verify that the user is marked as authenticated in the session
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['_user_id'], str(self.user_id))
        
        return response

    @patch('utils.get_movie_details')
    def test_add_movie_to_watchlist(self, mock_get_movie_details):
        """Test adding a movie to the watchlist."""
        mock_get_movie_details.return_value = {'id': 1, 'title': 'Test Movie'}

        with self.client:
            # Log in the user
            self.login()

            movie_id = 1
            response = self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)

            # Check if the response is successful
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Movie added to watchlist.", response.data)

            with app.app_context():
                user_movie = UserMovies.query.filter_by(
                    user_id=self.user_id, movie_id=movie_id, category='watchlist'
                ).first()
                self.assertIsNotNone(user_movie)

    @patch('utils.get_movie_details')
    def test_remove_movie_from_watchlist(self, mock_get_movie_details):
        """Test removing a movie from the watchlist."""
        mock_get_movie_details.return_value = {'id': 1, 'title': 'Test Movie'}

        with self.client:
            # Log in the user
            self.login()

            movie_id = 1
            # First, add the movie to the watchlist
            add_response = self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)
            self.assertEqual(add_response.status_code, 200)
            self.assertIn(b"Movie added to watchlist.", add_response.data)

            # Now, remove the movie from the watchlist
            remove_response = self.client.post(f'/watchlist/remove/{movie_id}', follow_redirects=True)

            # Check if the response is successful
            self.assertEqual(remove_response.status_code, 200)
            self.assertIn(b"Movie removed from watchlist.", remove_response.data)

            with app.app_context():
                user_movie = UserMovies.query.filter_by(
                    user_id=self.user_id, movie_id=movie_id, category='watchlist'
                ).first()
                self.assertIsNone(user_movie)

    @patch('utils.get_movie_details')
    def test_add_movie_to_favorites(self, mock_get_movie_details):
        """Test adding a movie to the favorites."""
        mock_get_movie_details.return_value = {'id': 1, 'title': 'Test Movie'}

        with self.client:
            # Log in the user
            self.login()

            movie_id = 1
            response = self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)

            # Check if the response is successful
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Movie added to favorites.", response.data)

            with app.app_context():
                user_movie = UserMovies.query.filter_by(
                    user_id=self.user_id, movie_id=movie_id, category='favorites'
                ).first()
                self.assertIsNotNone(user_movie)

    @patch('utils.get_movie_details')
    def test_remove_movie_from_favorites(self, mock_get_movie_details):
        """Test removing a movie from the favorites."""
        mock_get_movie_details.return_value = {'id': 1, 'title': 'Test Movie'}

        with self.client:
            # Log in the user
            self.login()

            movie_id = 1
            # First, add the movie to the favorites
            add_response = self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)
            self.assertEqual(add_response.status_code, 200)
            self.assertIn(b"Movie added to favorites.", add_response.data)

            # Now, remove the movie from the favorites
            remove_response = self.client.post(f'/favorites/remove/{movie_id}', follow_redirects=True)

            # Check if the response is successful
            self.assertEqual(remove_response.status_code, 200)
            self.assertIn(b"Movie removed from favorites.", remove_response.data)

            with app.app_context():
                user_movie = UserMovies.query.filter_by(
                    user_id=self.user_id, movie_id=movie_id, category='favorites'
                ).first()
                self.assertIsNone(user_movie)

    def tearDown(self):
        """Clean up after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

if __name__ == '__main__':
    unittest.main()
