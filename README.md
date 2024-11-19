Movie Recommendation System
This project, developed as part of NEF 3002 - Applied Project 2 (Winter Block), is a collaborative effort by Group 13:

Safal Karki (s4680098)
Abin Bajracharya (s4675959)
Anup Regmi (s4680730)
Pravesh Uprety (s4677960)
The application is a Flask-based web platform that enables users to explore, rate, and review movies, offering personalized recommendations based on user feedback.

Features
User Authentication: Secure registration and login system to manage user accounts.
Movie Exploration: Browse and search for movies with detailed information fetched from the TMDB API.
Ratings and Reviews: Users can rate movies and write reviews to share their opinions.
Personalized Recommendations: Receive movie suggestions tailored to individual preferences based on user interactions.
Watchlist and Favorites: Manage a personal watchlist and mark favorite movies for easy access.
Installation
To set up the Movie Recommendation System locally, follow these steps:

Clone the Repository:

bash
Copy code
git clone https://github.com/kingnw/movies.git
cd movies
Create and Activate a Virtual Environment:

bash
Copy code
python3 -m venv venv
source venv/bin/activate
Upgrade pip:

bash
Copy code
pip install --upgrade pip
Install Dependencies:

bash
Copy code
pip install -r requirements.txt
If a requirements.txt file is not provided, install the necessary packages individually:

bash
Copy code
pip install flask
pip install flask_sqlalchemy
pip install requests
pip install pandas
pip install scikit-learn
pip install flask_login
pip install flask_caching
pip install pytest pytest-mock
pip install pytest-flask
pip install python-dotenv
pip install beautifulsoup4
Set Up Environment Variables:

Create a .env file in the project root directory and add the following variables:

env
Copy code
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
TMDB_API_KEY=your_tmdb_api_key
Replace your_secret_key with a secure key of your choice and your_tmdb_api_key with your TMDB API key.

Initialize the Database:

bash
Copy code
flask db init
flask db migrate
flask db upgrade
Run the Application:

bash
Copy code
flask run
The application will be accessible at http://127.0.0.1:5000/.

Usage
Register: Create a new account to access personalized features.
Login: Access your account to rate, review, and receive recommendations.
Explore Movies: Browse the movie catalog and view detailed information.
Rate and Review: Share your thoughts by rating and reviewing movies.
Manage Watchlist and Favorites: Keep track of movies you want to watch and your favorites.
Get Recommendations: Discover new movies tailored to your tastes.
Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a new branch for your feature or bugfix.
Commit your changes with clear messages.
Push your branch and create a pull request.
Please ensure your code follows the project's coding standards and includes appropriate tests.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgments
TMDB API for providing movie data.
Flask for the web framework.
Bootstrap for front-end components.
Thank you for using the Movie Recommendation System! If you have any questions or feedback, feel free to open an issue or contact the repository owner.
