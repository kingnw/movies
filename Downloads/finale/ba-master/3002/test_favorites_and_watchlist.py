import unittest
from app import app, db
from models import User, UserMovies
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Enforce foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class WatchlistFavoritesTestCase(unittest.TestCase):
    """Test case for watchlist and favorites functionality."""

    def setUp(self):
        """Set up the test environment."""
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.testing = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()  # Ensure all tables are dropped before creating
            db.create_all()  # Create all tables
            user = User(username='testuser', password='testpassword')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        """Clean up after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_user(self):
        """Helper method to log in a user."""
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        return response

    def test_add_movie_to_watchlist(self):
        """Test adding a movie to the watchlist."""
        self.login_user()
        movie_id = 123
        response = self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user_movie = UserMovies.query.filter_by(
                user_id=1,
                movie_id=movie_id,
                category='watchlist'
            ).first()
            self.assertIsNotNone(user_movie)

    def test_remove_movie_from_watchlist(self):
        """Test removing a movie from the watchlist."""
        self.login_user()
        movie_id = 123

        # Add the movie first
        self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)

        # Remove the movie
        response = self.client.post(f'/watchlist/remove/{movie_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user_movie = UserMovies.query.filter_by(
                user_id=1,
                movie_id=movie_id,
                category='watchlist'
            ).first()
            self.assertIsNone(user_movie)

    def test_view_watchlist(self):
        """Test viewing the watchlist."""
        self.login_user()
        movie_id = 123

        # Add the movie
        self.client.post(f'/watchlist/add/{movie_id}', follow_redirects=True)

        # View the watchlist
        response = self.client.get('/watchlist', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your Watchlist", response.data)

    def test_add_movie_to_favorites(self):
        """Test adding a movie to favorites."""
        self.login_user()
        movie_id = 456
        response = self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user_movie = UserMovies.query.filter_by(
                user_id=1,
                movie_id=movie_id,
                category='favorites'
            ).first()
            self.assertIsNotNone(user_movie)

    def test_remove_movie_from_favorites(self):
        """Test removing a movie from favorites."""
        self.login_user()
        movie_id = 456

        # Add the movie first
        self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)

        # Remove the movie
        response = self.client.post(f'/favorites/remove/{movie_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user_movie = UserMovies.query.filter_by(
                user_id=1,
                movie_id=movie_id,
                category='favorites'
            ).first()
            self.assertIsNone(user_movie)

    def test_view_favorites(self):
        """Test viewing favorites."""
        self.login_user()
        movie_id = 456

        # Add the movie
        self.client.post(f'/favorites/add/{movie_id}', follow_redirects=True)

        # View favorites
        response = self.client.get('/favorites', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your Favorites", response.data)


if __name__ == '__main__':
    unittest.main()
