# tests/test_filters.py

import unittest
from app import create_app
from models import db, Movie
from config import TestingConfig
from bs4 import BeautifulSoup

class FilterSortTestCase(unittest.TestCase):
    def setUp(self):
        """Set up a test client and initialize a new database."""
        self.app = create_app('config.TestingConfig')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Add a single sample movie to the database
        self.populate_sample_data()

    def tearDown(self):
        """Remove the database session and drop all tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def populate_sample_data(self):
        """Populate the database with one sample movie."""
        movie = Movie(
            title="Movie A",
            year=2000,
            genre="Action",
            rating=8.0,
            language="English"
        )
        db.session.add(movie)
        db.session.commit()

    def test_filter_by_genre(self):
        """Test filtering movies by genre."""
        response = self.client.post('/recommend', data={
            'genre': 'Action'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.data, 'html.parser')
        movie_titles = [tag.text.strip() for tag in soup.find_all('h5', class_='card-title')]

        self.assertIn('Movie A', movie_titles)

    def test_filter_by_genre_no_results(self):
        """Test filtering movies by a genre that does not match."""
        response = self.client.post('/recommend', data={
            'genre': 'Drama'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.data, 'html.parser')
        # Check if 'No movies found' message is displayed
        no_movies_msg = soup.find('p', {'id': 'no-movies-msg'})
        self.assertIsNotNone(no_movies_msg)
        self.assertEqual(no_movies_msg.text.strip(), 'No movies found.')

    def test_filter_by_language(self):
        """Test filtering movies by language."""
        response = self.client.post('/recommend', data={
            'language': 'English'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.data, 'html.parser')
        movie_titles = [tag.text.strip() for tag in soup.find_all('h5', class_='card-title')]

        self.assertIn('Movie A', movie_titles)

    def test_filter_by_language_no_results(self):
        """Test filtering movies by a language that does not match."""
        response = self.client.post('/recommend', data={
            'language': 'French'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.data, 'html.parser')
        no_movies_msg = soup.find('p', {'id': 'no-movies-msg'})
        self.assertIsNotNone(no_movies_msg)
        self.assertEqual(no_movies_msg.text.strip(), 'No movies found.')

    def test_combined_filters(self):
        """Test filtering movies with multiple criteria."""
        response = self.client.post('/recommend', data={
            'genre': 'Action',
            'language': 'English'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.data, 'html.parser')
        movie_titles = [tag.text.strip() for tag in soup.find_all('h5', class_='card-title')]

        self.assertIn('Movie A', movie_titles)

    def test_combined_filters_no_results(self):
        """Test filters that result in no matching movies."""
        response = self.client.post('/recommend', data={
            'genre': 'Action',
            'language': 'French'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.data, 'html.parser')
        no_movies_msg = soup.find('p', {'id': 'no-movies-msg'})
        self.assertIsNotNone(no_movies_msg)
        self.assertEqual(no_movies_msg.text.strip(), 'No movies found.')

if __name__ == '__main__':
    unittest.main()