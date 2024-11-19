import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from models import db, Review, UserMovies
from recommendation import (
    get_personalized_recommendations,
    get_collaborative_recommendations,
    get_similar_users,
    calculate_similarity,
    get_genre_similarity,
    get_similar_movies_for_details,
    get_recommended_movies,
)
from datetime import datetime

# Setting up the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class TestRecommendation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the Flask app context and initialize the database."""
        with app.app_context():
            db.create_all()
            # Add some mock reviews for testing
            db.session.add(Review(user_id=1, movie_id=101, rating=9, created_at=datetime.utcnow()))
            db.session.add(Review(user_id=2, movie_id=101, rating=8, created_at=datetime.utcnow()))
            db.session.add(Review(user_id=3, movie_id=102, rating=7, created_at=datetime.utcnow()))
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        """Tear down the database after all tests."""
        with app.app_context():
            db.drop_all()

    def setUp(self):
        """Set up the app context for each individual test."""
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Pop the app context after each test."""
        self.app_context.pop()

    @patch('recommendation.get_movie_details')
    @patch('recommendation.get_similar_users')
    def test_collaborative_recommendations(self, mock_get_similar_users, mock_get_movie_details):
        print("Setting up mocks for collaborative recommendations...")

        # Mock similar users for collaborative filtering
        mock_get_similar_users.return_value = [2, 3]
        print("Mock similar users created for collaborative filtering.")

        # Mock movie details for the recommended movies from similar users
        mock_get_movie_details.side_effect = lambda movie_id: {
            'id': movie_id,
            'title': f'Movie Title {movie_id}',
            'genre_ids': [1, 2]
        }
        print("Mock movie details are set for collaborative filtering.")

        # Perform the collaborative recommendation test
        user_mock = MagicMock(id=1, is_authenticated=True)
        recommendations = get_collaborative_recommendations(user_mock.id)

        # Debug print to verify recommendations
        print(f"Collaborative recommendations: {recommendations}")

        # Assert that recommendations are returned
        self.assertGreater(len(recommendations), 0, "No collaborative recommendations were generated.")

    @patch('recommendation.get_movie_recommendations')
    @patch('recommendation.get_movie_details')
    def test_content_based_recommendations(self, mock_get_movie_details, mock_get_movie_recommendations):
        print("Setting up mocks for content-based recommendations...")

        # Mock movie details for the user's recently rated movies
        mock_get_movie_details.side_effect = lambda movie_id: {
            'id': movie_id,
            'title': f'Movie Title {movie_id}',
            'genre_ids': [1, 2]
        }
        print("Mock movie details are set.")

        # Mock TMDB recommendations based on these movies
        mock_get_movie_recommendations.side_effect = [
            [{'id': 201, 'title': 'Recommended Movie 1', 'type': 'content'}, {'id': 202, 'title': 'Recommended Movie 2', 'type': 'content'}]
        ]
        print("Mock TMDB recommendations for rated movies are set.")

        # Perform the content-based recommendation test
        user_mock = MagicMock(id=1, is_authenticated=True)
        recommendations = get_personalized_recommendations(user_mock)

        # Debug print to verify recommendations
        print(f"Content-based recommendations: {recommendations}")

        # Assert that recommendations are returned and are correctly marked as 'content'
        self.assertGreater(len(recommendations), 0, "No content-based recommendations were generated.")
        self.assertTrue(all(rec['type'] == 'content' for rec in recommendations))

    @patch('recommendation.Review.query.filter')
    def test_calculate_similarity(self, mock_filter):
        print("Setting up mock for calculate_similarity...")

        # Mock user reviews
        mock_user_review = MagicMock(user_id=1, movie_id=101, rating=9)
        mock_other_user_review = MagicMock(user_id=2, movie_id=101, rating=8)
        mock_filter.side_effect = [[mock_user_review], [mock_other_user_review]]

        similarity_score = calculate_similarity(1, 2)
        print(f"Similarity score: {similarity_score}")

        self.assertGreaterEqual(similarity_score, 0, "Similarity score calculation failed.")

    @patch('recommendation.get_movie_details')
    @patch('recommendation.Review.query.filter')
    def test_get_genre_similarity(self, mock_filter, mock_get_movie_details):
        print("Setting up mock for get_genre_similarity...")

        # Mock reviews
        mock_user_review = MagicMock(user_id=1, movie_id=101, rating=9)
        mock_other_user_review = MagicMock(user_id=2, movie_id=102, rating=8)
        mock_filter.side_effect = [[mock_user_review], [mock_other_user_review]]

        # Mock movie details to include genres
        mock_get_movie_details.side_effect = lambda movie_id: {
            'id': movie_id,
            'genre_ids': [1, 2]
        }

        genre_similarity = get_genre_similarity(1, 2)
        print(f"Genre similarity: {genre_similarity}")

        self.assertGreaterEqual(genre_similarity, 0, "Genre similarity calculation failed.")

    @patch('requests.get')
    def test_get_similar_movies_for_details(self, mock_get):
        print("Setting up mock for get_similar_movies_for_details...")

        # Mock TMDB API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [{'id': 201, 'title': 'Recommended Movie 1'}, {'id': 202, 'title': 'Recommended Movie 2'}]
        }
        mock_get.return_value = mock_response

        recommendations = get_similar_movies_for_details(101)
        print(f"Similar movies: {recommendations}")

        self.assertGreater(len(recommendations), 0, "No similar movies found.")

    @patch('requests.get')
    def test_get_recommended_movies(self, mock_get):
        print("Setting up mock for get_recommended_movies...")

        # Mock TMDB API response for trending movies
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [{'id': 301, 'title': 'Trending Movie 1'}, {'id': 302, 'title': 'Trending Movie 2'}]
        }
        mock_get.return_value = mock_response

        user_mock = MagicMock(id=1, is_authenticated=False)
        recommendations = get_recommended_movies(user_mock)
        print(f"Recommended movies: {recommendations}")

        self.assertGreater(len(recommendations), 0, "No recommended movies found.")


if __name__ == '__main__':
    unittest.main()
