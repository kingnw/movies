# tests/test_recommendation.py

import pytest
from unittest.mock import MagicMock
from recommendation import (
    get_similar_movies_for_details,
    get_recommended_movies,
    get_genre_based_recommendations,
    get_user_preferred_genres,
    get_movie_recommendations,
    get_personalized_recommendations,
    process_movie_results
)
from models import UserMovies, Review

# 1. Testing get_similar_movies_for_details
def test_get_similar_movies_for_details_success(mocker):
    movie_id = 123
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [
            {
                'id': 1,
                'vote_average': 8.0,
                'poster_path': '/path.jpg',
                'backdrop_path': '/backdrop.jpg'
            }
        ]
    }

    # Mock requests.get and process_movie_results
    mock_get = mocker.patch('recommendation.requests.get', return_value=mock_response)
    mock_process = mocker.patch('recommendation.process_movie_results', return_value=[{
        'id': 1,
        'rating': 8.0,
        'poster': 'https://image.tmdb.org/t/p/original/path.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop.jpg'
    }])

    # Call the function
    result = get_similar_movies_for_details(movie_id)

    # Assertions
    mock_get.assert_called_once_with(
        f'https://api.themoviedb.org/3/movie/{movie_id}/recommendations',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'page': 1
        }
    )
    mock_process.assert_called_once_with(mock_response)
    assert result == [{
        'id': 1,
        'rating': 8.0,
        'poster': 'https://image.tmdb.org/t/p/original/path.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop.jpg'
    }]

def test_get_similar_movies_for_details_failure(mocker):
    movie_id = 123
    mock_response = MagicMock()
    mock_response.status_code = 404

    # Mock requests.get and process_movie_results
    mock_get = mocker.patch('recommendation.requests.get', return_value=mock_response)
    mock_process = mocker.patch('recommendation.process_movie_results', return_value=[])

    # Call the function
    result = get_similar_movies_for_details(movie_id)

    # Assertions
    mock_get.assert_called_once_with(
        f'https://api.themoviedb.org/3/movie/{movie_id}/recommendations',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'page': 1
        }
    )
    mock_process.assert_called_once_with(mock_response)
    assert result == []

# 2. Testing get_recommended_movies
def test_get_recommended_movies_with_favorites(mocker):
    user = MagicMock()
    user.is_authenticated = True
    user.id = 1

    # Mock the database query for favorites
    mock_favorite = MagicMock()
    mock_favorite.movie_id = 456

    mock_filter_by = mocker.patch('models.UserMovies.query.filter_by')
    mock_order = mock_filter_by.return_value.order_by.return_value
    mock_order.first.return_value = mock_favorite

    # Mock get_movie_details and get_movie_recommendations
    mock_get_movie_details = mocker.patch('recommendation.get_movie_details', return_value={'title': 'Test Movie'})
    mock_get_movie_recommendations = mocker.patch('recommendation.get_movie_recommendations', return_value=[{'id': 2, 'title': 'Recommended Movie'}])

    # Call the function
    result = get_recommended_movies(user)

    # Assertions
    assert result == [{'id': 2, 'title': 'Recommended Movie'}]
    mock_get_movie_details.assert_called_with(456)
    mock_get_movie_recommendations.assert_called_with('Test Movie')

def test_get_recommended_movies_no_favorites_watchlist(mocker):
    user = MagicMock()
    user.is_authenticated = True
    user.id = 1

    # Mock the database query for favorites and watchlist
    mock_filter_by = mocker.patch('models.UserMovies.query.filter_by')
    mock_order = mock_filter_by.return_value.order_by.return_value
    mock_order.first.side_effect = [None, None]  # No favorites or watchlist

    # Mock the trending API call
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [
            {
                'id': 3,
                'vote_average': 7.5,
                'poster_path': '/path3.jpg',
                'backdrop_path': '/backdrop3.jpg'
            }
        ]
    }
    mock_requests_get = mocker.patch('recommendation.requests.get', return_value=mock_response)
    mock_process_movie_results = mocker.patch('recommendation.process_movie_results', return_value=[{
        'id': 3,
        'rating': 7.5,
        'poster': 'https://image.tmdb.org/t/p/original/path3.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop3.jpg'
    }])

    # Call the function
    result = get_recommended_movies(user)

    # Assertions
    assert result == [{
        'id': 3,
        'rating': 7.5,
        'poster': 'https://image.tmdb.org/t/p/original/path3.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop3.jpg'
    }]
    mock_requests_get.assert_called_once_with(
        'https://api.themoviedb.org/3/trending/movie/week',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'page': 1
        }
    )
    mock_process_movie_results.assert_called_once_with(mock_response)

def test_get_recommended_movies_unauthenticated(mocker):
    user = MagicMock()
    user.is_authenticated = False

    # Mock the trending API call
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [
            {
                'id': 4,
                'vote_average': 6.0,
                'poster_path': '/path4.jpg',
                'backdrop_path': '/backdrop4.jpg'
            }
        ]
    }
    mock_requests_get = mocker.patch('recommendation.requests.get', return_value=mock_response)
    mock_process_movie_results = mocker.patch('recommendation.process_movie_results', return_value=[{
        'id': 4,
        'rating': 6.0,
        'poster': 'https://image.tmdb.org/t/p/original/path4.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop4.jpg'
    }])

    # Call the function
    result = get_recommended_movies(user)

    # Assertions
    assert result == [{
        'id': 4,
        'rating': 6.0,
        'poster': 'https://image.tmdb.org/t/p/original/path4.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop4.jpg'
    }]
    mock_requests_get.assert_called_once_with(
        'https://api.themoviedb.org/3/trending/movie/week',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'page': 1
        }
    )
    mock_process_movie_results.assert_called_once_with(mock_response)

# 3. Testing get_genre_based_recommendations
def test_get_genre_based_recommendations_success(mocker):
    genres = [28, 12]  # Example genre IDs
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [
            {
                'id': 5,
                'vote_average': 7.2,
                'poster_path': '/path5.jpg',
                'backdrop_path': '/backdrop5.jpg'
            }
        ]
    }
    mock_requests_get = mocker.patch('recommendation.requests.get', return_value=mock_response)
    mock_process_movie_results = mocker.patch('recommendation.process_movie_results', return_value=[{
        'id': 5,
        'rating': 7.2,
        'poster': 'https://image.tmdb.org/t/p/original/path5.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop5.jpg'
    }])

    # Call the function
    result = get_genre_based_recommendations(genres)

    # Assertions
    assert result == [{
        'id': 5,
        'rating': 7.2,
        'poster': 'https://image.tmdb.org/t/p/original/path5.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop5.jpg'
    }]
    mock_requests_get.assert_called_once_with(
        'https://api.themoviedb.org/3/discover/movie',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'sort_by': 'popularity.desc',
            'with_genres': '28,12',
            'page': 1
        }
    )
    mock_process_movie_results.assert_called_once_with(mock_response)

# 4. Testing get_user_preferred_genres
def test_get_user_preferred_genres_with_genres(mocker):
    user = MagicMock()
    user.id = 1

    # Mock UserMovies.query.filter().all()
    mock_user_movie = MagicMock()
    mock_user_movie.movie_id = 789

    mock_filter = mocker.patch('models.UserMovies.query.filter')
    mock_filter.return_value.all.return_value = [mock_user_movie]

    # Mock get_movie_details
    mock_get_movie_details = mocker.patch('recommendation.get_movie_details', return_value={'genre_ids': [28, 12]})

    # Call the function
    result = get_user_preferred_genres(user)

    # Assertions
    assert set(result) == {28, 12}
    mock_filter.assert_called_once_with(
        UserMovies.user_id == user.id,
        UserMovies.category.in_(['watchlist', 'favorites'])
    )
    mock_get_movie_details.assert_called_with(789)

def test_get_user_preferred_genres_no_genres(mocker):
    user = MagicMock()
    user.id = 2

    # Mock UserMovies.query.filter().all()
    mock_filter = mocker.patch('models.UserMovies.query.filter')
    mock_filter.return_value.all.return_value = []

    # Call the function
    result = get_user_preferred_genres(user)

    # Assertions
    assert result is None
    mock_filter.assert_called_once_with(
        UserMovies.user_id == user.id,
        UserMovies.category.in_(['watchlist', 'favorites'])
    )

# 5. Testing get_movie_recommendations
def test_get_movie_recommendations_success(mocker):
    movie_title = "Inception"
    
    # Mock search API call
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        'results': [{'id': 550}]  # Example movie ID
    }

    # Mock recommendations API call
    mock_rec_response = MagicMock()
    mock_rec_response.status_code = 200
    mock_rec_response.json.return_value = {
        'results': [
            {
                'id': 551,
                'vote_average': 8.1,
                'poster_path': '/path551.jpg',
                'backdrop_path': '/backdrop551.jpg'
            }
        ]
    }

    mock_requests_get = mocker.patch('recommendation.requests.get', side_effect=[mock_search_response, mock_rec_response])
    mock_process_movie_results = mocker.patch('recommendation.process_movie_results', return_value=[{
        'id': 551,
        'rating': 8.1,
        'poster': 'https://image.tmdb.org/t/p/original/path551.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop551.jpg'
    }])

    # Call the function
    result = get_movie_recommendations(movie_title)

    # Assertions
    assert result == [{
        'id': 551,
        'rating': 8.1,
        'poster': 'https://image.tmdb.org/t/p/original/path551.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/original/backdrop551.jpg'
    }]
    assert mock_requests_get.call_count == 2
    mock_requests_get.assert_any_call(
        'https://api.themoviedb.org/3/search/movie',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'query': movie_title,
            'page': 1,
            'include_adult': False
        }
    )
    mock_requests_get.assert_any_call(
        'https://api.themoviedb.org/3/movie/550/recommendations',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'page': 1
        }
    )
    mock_process_movie_results.assert_called_once_with(mock_rec_response)

def test_get_movie_recommendations_no_search_results(mocker):
    movie_title = "Unknown Movie"
    
    # Mock search API call with no results
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {'results': []}

    mock_requests_get = mocker.patch('recommendation.requests.get', return_value=mock_search_response)
    mock_process_movie_results = mocker.patch('recommendation.process_movie_results', return_value=[])

    # Call the function
    result = get_movie_recommendations(movie_title)

    # Assertions
    assert result == []
    mock_requests_get.assert_called_once_with(
        'https://api.themoviedb.org/3/search/movie',
        params={
            'api_key': '9ba93d1cf5e3054788a377f636ea1033',
            'language': 'en-US',
            'query': movie_title,
            'page': 1,
            'include_adult': False
        }
    )
    mock_process_movie_results.assert_called_once_with(mock_search_response)

# 6. Testing get_personalized_recommendations
def test_get_personalized_recommendations(mocker):
    user = MagicMock()
    user.id = 1

    # Mock Review.query.filter().order_by().limit().all()
    mock_review1 = MagicMock(movie_id=101, rating=5, created_at='2023-10-01')
    mock_review2 = MagicMock(movie_id=102, rating=4, created_at='2023-09-01')
    mock_review3 = MagicMock(movie_id=103, rating=4, created_at='2023-08-01')
    mock_review4 = MagicMock(movie_id=104, rating=5, created_at='2023-07-01')
    
    mock_filter = mocker.patch('models.Review.query.filter')
    mock_filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        mock_review1, mock_review2, mock_review3, mock_review4
    ]

    # Mock get_movie_details
    def get_movie_details_side_effect(movie_id):
        return {'title': f'Movie {movie_id}'}
    mock_get_movie_details = mocker.patch('recommendation.get_movie_details', side_effect=get_movie_details_side_effect)

    # Mock get_movie_recommendations
    def get_movie_recommendations_side_effect(title):
        movie_id = int(title.split()[-1])
        return [{'id': movie_id + 1000, 'title': f'Rec for {title}'}]
    mock_get_movie_recommendations = mocker.patch('recommendation.get_movie_recommendations', side_effect=get_movie_recommendations_side_effect)

    # Call the function
    result = get_personalized_recommendations(user)

    # Assertions
    expected = [
        {'id': 1101, 'title': 'Rec for Movie 101'},
        {'id': 1102, 'title': 'Rec for Movie 102'},
        {'id': 1103, 'title': 'Rec for Movie 103'},
        {'id': 1104, 'title': 'Rec for Movie 104'}
    ]
    assert result == expected
    assert mock_filter.call_count == 1
    mock_get_movie_details.assert_any_call(101)
    mock_get_movie_details.assert_any_call(102)
    mock_get_movie_details.assert_any_call(103)
    mock_get_movie_details.assert_any_call(104)
    assert mock_get_movie_recommendations.call_count == 4
    mock_get_movie_recommendations.assert_any_call('Movie 101')
    mock_get_movie_recommendations.assert_any_call('Movie 102')
    mock_get_movie_recommendations.assert_any_call('Movie 103')
    mock_get_movie_recommendations.assert_any_call('Movie 104')

# 7. Testing process_movie_results
def test_process_movie_results_success():
    from recommendation import process_movie_results  # Import inside function to avoid conflicts
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [
            {
                'id': 6,
                'vote_average': 9.0,
                'poster_path': '/poster6.jpg',
                'backdrop_path': '/backdrop6.jpg'
            },
            {
                'id': 7,
                'vote_average': 5.5,
                'poster_path': None,
                'backdrop_path': None
            }
        ]
    }

    # Call the function
    result = process_movie_results(mock_response)

    # Assertions
    assert result == [
        {
            'id': 6,
            'rating': 9.0,
            'poster': 'https://image.tmdb.org/t/p/original/poster6.jpg',
            'backdrop': 'https://image.tmdb.org/t/p/original/backdrop6.jpg'
        },
        {
            'id': 7,
            'rating': 5.5,
            'poster': 'https://via.placeholder.com/500x750?text=No+Image',
            'backdrop': 'https://via.placeholder.com/1280x720?text=No+Image'
        }
    ]

def test_process_movie_results_failure(mocker):
    from recommendation import process_movie_results  # Import inside function to avoid conflicts
    mock_response = MagicMock()
    mock_response.status_code = 500

    # Call the function
    result = process_movie_results(mock_response)

    # Assertions
    assert result == []