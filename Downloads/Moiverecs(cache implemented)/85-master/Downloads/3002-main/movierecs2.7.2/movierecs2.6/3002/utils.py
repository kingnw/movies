# utils.py
from flask import Flask 
import requests
import os
from models import Review
from flask_caching import Cache

cache = Cache()

API_KEY = os.environ.get('TMDB_API_KEY', '9ba93d1cf5e3054788a377f636ea1033')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def get_movie_details(movie_id):
    """Fetches detailed information for a specific movie including main characters and director."""
    url = f'{TMDB_BASE_URL}/movie/{movie_id}'
    params = {
        'api_key': API_KEY,
        'language': 'en-US'
    }
    response = requests.get(url, params=params)

    # Fetch credits to get director and main characters
    credits_url = f'{TMDB_BASE_URL}/movie/{movie_id}/credits'
    credits_response = requests.get(credits_url, params=params)

    if response.status_code == 200:
        movie = response.json()
        movie['rating'] = movie.get('vote_average', 'N/A')

        # Handle poster and backdrop images
        poster_path = movie.get('poster_path')
        movie['poster'] = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"
        backdrop_path = movie.get('backdrop_path')
        movie['backdrop'] = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else "https://via.placeholder.com/1280x720?text=No+Image"

        # Include original_language for filtering
        movie['original_language'] = movie.get('original_language', 'N/A')
        movie['genre_ids'] = [genre['id'] for genre in movie.get('genres', [])]

        # Check if credits data is available
        if credits_response.status_code == 200:
            credits = credits_response.json()

            # Extract director's name
            director = next((member['name'] for member in credits.get('crew', []) if member.get('job') == 'Director'), "Not Available")
            movie['director'] = director

            # Extract main characters (first 5 actors)
            main_cast = [member['name'] for member in credits.get('cast', [])[:5]]
            movie['main_characters'] = main_cast if main_cast else ["No main characters available"]

        return movie

    return None

def calculate_avg_rating(movie_id):
    """Calculates the average rating for a movie based on user reviews."""
    reviews = Review.query.filter_by(movie_id=movie_id).all()
    if reviews:
        avg_rating = sum([review.rating for review in reviews]) / len(reviews)
        return round(avg_rating, 1)
    return "No ratings yet"

def get_similar_movie_ratings(recommendations):
    """Calculates average rating for each movie in the recommendations."""
    for movie in recommendations:
        movie['average_rating'] = calculate_avg_rating(movie['id'])
    return recommendations

def get_movie_recommendations(movie_title):
    """Fetches recommendations based on a specific movie title."""
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
