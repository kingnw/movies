# recommendation.py

import requests
import os
from models import UserMovies, Review  # Import your models to access user watchlist/favorites and reviews
from utils import get_movie_details, get_movie_recommendations
from datetime import datetime


# TMDB API Key and base URL
API_KEY = os.environ.get('TMDB_API_KEY', '9ba93d1cf5e3054788a377f636ea1033')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def get_similar_movies_for_details(movie_id):
    """Fetches movies similar to a specific movie for the movie details page."""
    recommendations_url = f'{TMDB_BASE_URL}/movie/{movie_id}/recommendations'
    params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'page': 1
    }
    response = requests.get(recommendations_url, params=params)
    return process_movie_results(response)
def get_recommended_movies(user=None):
    if user and user.is_authenticated:
        # Retrieve the most recent favorite or fallback to the watchlist
        last_favorite = UserMovies.query.filter_by(user_id=user.id, category='favorites') \
                                        .order_by(UserMovies.id.desc()).first()
        
        last_movie = last_favorite or UserMovies.query.filter_by(user_id=user.id, category='watchlist') \
                                                      .order_by(UserMovies.id.desc()).first()
        
        if last_movie:
            movie = get_movie_details(last_movie.movie_id)
            if movie:
                recommendations = get_movie_recommendations(movie['title'])
                if recommendations:
                    return recommendations
                else:
                    print("No recommendations returned for:", movie['title'])
            else:
                print("Movie details not found for movie ID:", last_movie.movie_id)

    # Default to trending movies if no user or no specific genres in watchlist/favorites
    url = f'{TMDB_BASE_URL}/trending/movie/week'
    params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'page': 1
    }
    response = requests.get(url, params=params)
    return process_movie_results(response)

def get_genre_based_recommendations(genres):
    """
    Fetches movies based on a list of genre IDs for personalized recommendations.
    """
    url = f'{TMDB_BASE_URL}/discover/movie'
    genre_ids = ','.join(map(str, genres))
    params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'sort_by': 'popularity.desc',
        'with_genres': genre_ids,
        'page': 1
    }
    response = requests.get(url, params=params)
    return process_movie_results(response)

def get_user_preferred_genres(user):
    """
    Retrieves a list of unique genre IDs from the user's watchlist and favorites.
    """
    user_movies = UserMovies.query.filter(
        UserMovies.user_id == user.id,
        UserMovies.category.in_(['watchlist', 'favorites'])
    ).all()
    
    genre_ids = set()
    for user_movie in user_movies:
        movie = get_movie_details(user_movie.movie_id)
        if movie:
            genre_ids.update(movie.get('genre_ids', []))
    
    return list(genre_ids) if genre_ids else None

def get_movie_recommendations(movie_title):
    """Fetches content-based recommendations based on a specific movie title."""
    search_url = f'{TMDB_BASE_URL}/search/movie'
    search_params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'query': movie_title,
        'page': 1,
        'include_adult': False
    }
    search_response = requests.get(search_url, params=search_params)
    if search_response.status_code == 200:
        search_results = search_response.json().get('results', [])
        if search_results:
            movie_id = search_results[0]['id']
            recommendations_url = f'{TMDB_BASE_URL}/movie/{movie_id}/recommendations'
            rec_params = {
                'api_key': API_KEY,
                'language': 'en-US',
                'page': 1
            }
            rec_response = requests.get(recommendations_url, params=rec_params)
            return process_movie_results(rec_response)
    return []


def get_personalized_recommendations(user):
    """
    Generates personalized movie recommendations based on the user's latest ratings.
    Recommends movies similar to the latest four movies that the user rated highly.
    """
    # Fetch user's top-rated movies ordered by the most recent reviews, limited to the latest 4
    top_rated_reviews = Review.query.filter(
        Review.user_id == user.id,
        Review.rating >= 4  # Adjust threshold for "highly rated" if needed
    ).order_by(Review.created_at.desc()).limit(4).all()

    recommended_movies = []
    for review in top_rated_reviews:
        # Get recommendations for each highly-rated movie
        similar_movies = get_movie_recommendations(get_movie_details(review.movie_id).get('title'))
        recommended_movies.extend(similar_movies)

    # Remove duplicates while maintaining the order and return the recommendations
    unique_recommendations = {movie['id']: movie for movie in recommended_movies}
    return list(unique_recommendations.values())

def process_movie_results(response):
    """Processes movie results from TMDB API responses to include images and ratings."""
    if response.status_code == 200:
        results = response.json().get('results', [])
        for movie in results:
            movie['rating'] = movie.get('vote_average', 'N/A')
            poster_path = movie.get('poster_path')
            movie['poster'] = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"
            backdrop_path = movie.get('backdrop_path')
            movie['backdrop'] = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else "https://via.placeholder.com/1280x720?text=No+Image"
        return results
    return []