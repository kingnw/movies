# recommendation.py

import requests
import os
from models import UserMovies, Review  
from utils import get_movie_details, get_movie_recommendations,cache
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import and_
import numpy as np

# TMDB API Key and Base URL for movie database interactions
API_KEY = os.environ.get('TMDB_API_KEY', '9ba93d1cf5e3054788a377f636ea1033')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Function to find similar users based on common highly-rated movies
def get_similar_users(user_id):
    """
    Find users who have rated at least 2 movies >= 4 in common with the current user.
    """
    # Fetch movies rated >= 4 by the current user
    current_user_movies = Review.query.filter_by(user_id=user_id).filter(Review.rating >= 5).all()
    current_user_movie_ids = {review.movie_id for review in current_user_movies}

    # Find users who share these moviesD
    similar_users = defaultdict(int)  # {user_id: shared_movie_count}

    # Find users who share these movies
    for movie_id in current_user_movie_ids:
        # Find other users who rated the same movie >= 5
        shared_reviews = Review.query.filter(
            Review.movie_id == movie_id,
            Review.rating >= 5
        ).all()

        for review in shared_reviews:
            if review.user_id != user_id:
                similar_users[review.user_id] += 1

    # Return users who have at least 2 shared movies
    return [user_id for user_id, count in similar_users.items() if count >= 2]

# Function to calculate similarity between two users
def calculate_similarity(user_id, other_user_id):
    """
    Calculate similarity between two users based on their ratings.
    """
    user_ratings = Review.query.filter_by(user_id=user_id).all()
    other_user_ratings = Review.query.filter_by(user_id=other_user_id).all()

    # Map movie IDs to ratings for both users
    user_movie_ratings = {r.movie_id: r.rating for r in user_ratings}
    other_movie_ratings = {r.movie_id: r.rating for r in other_user_ratings}

    # Find movies rated by both users
    common_movie_ids = set(user_movie_ratings.keys()).intersection(other_movie_ratings.keys())

    if not common_movie_ids:
        return 0  # No similarity if no shared movies

    # Extract ratings for common movies
    user_ratings_vector = np.array([user_movie_ratings[movie_id] for movie_id in common_movie_ids])
    other_ratings_vector = np.array([other_movie_ratings[movie_id] for movie_id in common_movie_ids])

    # Compute Pearson correlation if sufficient data is available
    if len(user_ratings_vector) > 1:  # Correlation requires at least two data points
        similarity = np.corrcoef(user_ratings_vector, other_ratings_vector)[0, 1]
        return 0 if np.isnan(similarity) else similarity

    return 0

# Function to compare genre preferences between two users
def get_genre_similarity(user_id, other_user_id):
    """
    Compare user preferences based on genres rated highly.
    """
    # Fetch highly-rated movies for both users
    user_movies = Review.query.filter_by(user_id=user_id).filter(Review.rating >= 4).all()
    other_user_movies = Review.query.filter_by(user_id=other_user_id).filter(Review.rating >= 4).all()

    # Extract genre IDs for each user's movies
    user_genres = set()
    for movie in user_movies:
        details = get_movie_details(movie.movie_id)
        user_genres.update(details.get('genre_ids', []))

    other_genres = set()
    for movie in other_user_movies:
        details = get_movie_details(movie.movie_id)
        other_genres.update(details.get('genre_ids', []))

    # Calculate genre overlap
    common_genres = user_genres.intersection(other_genres)
    return len(common_genres) / max(len(user_genres.union(other_genres)), 1)  # Avoid division by zero

# Function to generate collaborative recommendations
def get_collaborative_recommendations(user_id):
    """
    Generate collaborative recommendations by incorporating similarity and genre filtering.
    """
    similar_users = get_similar_users(user_id)
    print(f"[DEBUG] Similar users for user {user_id}: {similar_users}")
    recommendations = []

    # Fetch the genres preferred by the current user
    user_movies = Review.query.filter_by(user_id=user_id).filter(Review.rating >= 4).all()
    print(f"[DEBUG] Movies rated >=4 by user {user_id}: {[movie.movie_id for movie in user_movies]}")

    user_genres = set()
    for movie in user_movies:
        # Calculate similarity metrics
        details = get_movie_details(movie.movie_id)
        user_genres.update(details.get('genre_ids', []))

    for similar_user in similar_users:
        similarity_score = calculate_similarity(user_id, similar_user)
        genre_similarity = get_genre_similarity(user_id, similar_user)
        print(f"[DEBUG] Similarity score for user {similar_user}: {similarity_score}, Genre similarity: {genre_similarity}")
        # Process recommendations only if similarity conditions are met
        if similarity_score > 0.4 or genre_similarity > 0.1:
            similar_user_ratings = {
                review.movie_id: {'rating': review.rating, 'timestamp': review.created_at}
                for review in Review.query.filter_by(user_id=similar_user).filter(Review.rating >= 4).all()
            }

            for movie_id, details in similar_user_ratings.items():
                if movie_id not in [r.movie_id for r in Review.query.filter_by(user_id=user_id).all()]:
                    movie = get_movie_details(movie_id)
                    if movie:
                        print(f"[DEBUG] Adding collaborative recommendation: {movie['title']}")
                        # Check if the movie's genres align with the user's preferred genres
                        if set(movie['genre_ids']).intersection(user_genres):
                            recommendations.append(movie)
                            
    print(f"[DEBUG] Final collaborative recommendations for user {user_id}: {[movie['title'] for movie in recommendations]}")
    return recommendations

# Function to fetch similar movies for a given movie
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

# Function to generate general recommendations
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


def get_movie_recommendations(movie_title):
    """
    Fetch content-based recommendations for a specific movie using TMDB API with caching.
    """
    cache_key = f"movie_recommendations_{movie_title}"
    recommendations = cache.get(cache_key)

    if not recommendations:
        search_url = f"{TMDB_BASE_URL}/search/movie"
        search_params = {
            'api_key': API_KEY,
            'query': movie_title,
            'language': 'en-US',
            'page': 1
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

# Function to fetch personalized recommendations
def get_personalized_recommendations(user):
    """
    Generate personalized recommendations for a user based on:
    - Content-based filtering (recommendations for the last 2 movies rated >5).
    - Collaborative filtering (similar users' preferences).
    """
    if not user or not user.is_authenticated:
        return []

    # Initialize recommendation lists
    recommendations = []
    content_recommendations = []

    # Debugging the personalized recommendations
    print("Fetching content-based recommendations for user:", user.id)

    # Fetch the last 2 movies rated >5 by the user
    recent_reviews = Review.query.filter(
        Review.user_id == user.id,
        Review.rating > 5
    ).order_by(Review.created_at.desc()).limit(2).all()

    # Get content-based recommendations for these movies
    for review in recent_reviews:
        similar_movies = get_movie_recommendations(get_movie_details(review.movie_id).get('title'))
        for movie in similar_movies:
            movie['type'] = 'content'  # Mark as content-based
            content_recommendations.append(movie)

    # Get collaborative filtering recommendations
    collaborative_recs = get_collaborative_recommendations(user.id)
    for movie in collaborative_recs:
        movie['type'] = 'collaborative'  # Mark as collaborative
        recommendations.append(movie)

    # Combine content and collaborative recommendations
    recommendations.extend(content_recommendations)

    # Deduplicate recommendations by movie ID
    unique_recommendations = {movie['id']: movie for movie in recommendations}.values()

    return list(unique_recommendations)

# Function to process raw API results
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