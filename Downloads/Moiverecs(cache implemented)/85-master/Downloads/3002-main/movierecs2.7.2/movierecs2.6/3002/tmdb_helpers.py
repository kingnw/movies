# tmdb_helpers.py

import requests
import os
from utils import cache  # Import the cache instance from app.py
from hashlib import md5
import logging

API_KEY = os.environ.get('TMDB_API_KEY', '9ba93d1cf5e3054788a377f636ea1033')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Configure logging to write to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Writes logs to app.log file
        logging.StreamHandler()  # Also prints logs to the console
    ]
)

@cache.cached(timeout=300, key_prefix='top_rated_movies')
def get_top_rated_movies():
    url = f'{TMDB_BASE_URL}/movie/top_rated'
    return fetch_movies(url)

@cache.cached(timeout=300, key_prefix='new_released_movies')
def get_new_released_movies():
    url = f'{TMDB_BASE_URL}/movie/now_playing'
    return fetch_movies(url)

@cache.cached(timeout=300, key_prefix='trending_movies')
def get_trending_movies():
    url = f'{TMDB_BASE_URL}/trending/movie/week'
    return fetch_movies(url)

@cache.cached(timeout=86400, key_prefix='movie_genres')
def get_genres():
    url = f'{TMDB_BASE_URL}/genre/movie/list'
    params = {'api_key': API_KEY, 'language': 'en-US'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('genres', [])
    return []

@cache.memoize(timeout=3600)
def search_actor_movies(actor_name):
    actor_url = f'{TMDB_BASE_URL}/search/person'
    params = {'api_key': API_KEY, 'language': 'en-US', 'query': actor_name, 'include_adult': False}
    response = requests.get(actor_url, params=params)
    if response.status_code != 200:
        return []

    actor_movie_results = []
    actors = response.json().get('results', [])
    for actor in actors:
        person_id = actor.get('id')
        if person_id:
            credits_url = f'{TMDB_BASE_URL}/person/{person_id}/movie_credits'
            credits_response = requests.get(credits_url, params=params)
            if credits_response.status_code == 200:
                credits = credits_response.json().get('cast', [])
                actor_movie_results += process_movie_results(credits)

    unique_movies = {movie['id']: movie for movie in actor_movie_results}
    return list(unique_movies.values())
@cache.memoize(timeout=3600)  # Cache each unique search for 1 hour
def search_movie(query, filters=None):
    # Clean query
    keywords_to_remove = ["movies", "movie"]
    for keyword in keywords_to_remove:
        query = query.replace(keyword, "").strip()

    # Create a unique cache key for each query and filter combination
    filter_str = str(filters) if filters else ""
    cache_key = f"search_movie_{md5((query + filter_str).encode()).hexdigest()}"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        logging.info(f"Using cached results for search: {query} with filters: {filters}")
        return cached_result

    # Fetch movie search results
    movie_search_url = f'{TMDB_BASE_URL}/search/movie'
    params = {'api_key': API_KEY, 'language': 'en-US', 'query': query, 'include_adult': False}
    response = requests.get(movie_search_url, params=params)
    
    # Process results if response is successful
    title_results = process_movie_results(response.json().get('results', [])) if response.status_code == 200 else []
    
    # Fetch character results if available
    character_results = search_actor_movies(query)
    combined_results = {movie['id']: movie for movie in title_results + character_results}
    unique_movies = list(combined_results.values())

    # Apply filters (if any)
    if filters:
        unique_movies = apply_filters(unique_movies, filters)

    # Cache the final filtered results
    cache.set(cache_key, unique_movies, timeout=3600)  # 1-hour cache
    logging.info(f"Cached search results for {query} with filters {filters}")
    return unique_movies

def apply_filters(movies, filters):
    """Applies filters to the movie search results."""
    release_year = filters.get('release_year')
    rating = filters.get('rating')
    genre = filters.get('genre')
    language = filters.get('language')
    sort_by = filters.get('sort_by')

    if release_year:
        movies = [movie for movie in movies if movie.get('release_date', '').startswith(str(release_year))]
    if rating:
        try:
            rating = float(rating)
            movies = [movie for movie in movies if float(movie.get('rating', 0)) >= rating]
        except ValueError:
            pass
    if genre:
        genre = str(genre)
        movies = [movie for movie in movies if genre in [str(gid) for gid in movie.get('genre_ids', [])]]
    if language:
        movies = [movie for movie in movies if movie.get('original_language') == language]

    # Sorting based on sort_by criteria
    if sort_by:
        sort_key = {
            'rating_desc': lambda x: x.get('rating', 0),
            'rating_asc': lambda x: x.get('rating', 0),
            'release_date_desc': lambda x: x.get('release_date', ''),
            'release_date_asc': lambda x: x.get('release_date', ''),
            'title_asc': lambda x: x.get('title', '').lower(),
            'title_desc': lambda x: x.get('title', '').lower()
        }.get(sort_by)

        if sort_key:
            reverse = sort_by.endswith('_desc')
            movies.sort(key=sort_key, reverse=reverse)

    return movies

def fetch_movies(url):
    # Cache based on URL
    cache_key = f"fetch_movies_{url.split('/')[-1]}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logging.info(f"Using cached data for {url}")
        return cached_data

    params = {'api_key': API_KEY, 'language': 'en-US', 'page': 1}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        movies = process_movie_results(response.json().get('results', []))
        cache.set(cache_key, movies, timeout=300)  # Cache for 5 minutes
        return movies
    
    return []

def process_movie_results(results):
    movies = []
    for movie in results:
        movies.append({
            'id': movie.get('id'),
            'title': movie.get('title', 'No Title'),
            'rating': movie.get('vote_average', 'N/A'),
            'release_date': movie.get('release_date', 'N/A'),
            'original_language': movie.get('original_language', 'N/A'),
            'genre_ids': movie.get('genre_ids', []),
            'poster': f"https://image.tmdb.org/t/p/original{movie['poster_path']}" if movie.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image",
            'backdrop': f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}" if movie.get('backdrop_path') else "https://via.placeholder.com/1280x720?text=No+Image"
        })
    return movies
