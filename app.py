import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# TMDB API
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def tmdb_request(endpoint, params=None):

    if not TMDB_API_KEY:
        return None, "TMDB API key is not configured."

    if params is None:
        params = {}

    params["api_key"] = TMDB_API_KEY

    try:
        response = requests.get(
            TMDB_BASE_URL + endpoint,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        return response.json(), None

    except requests.exceptions.RequestException as e:

        return None, str(e)


def clean_movie(movie):

    return {
        "id": movie.get("id"),

        "title": movie.get(
            "title",
            "Unknown Movie"
        ),

        "release_date": movie.get(
            "release_date",
            "Unknown"
        ),

        "rating": round(
            float(movie.get("vote_average", 0)),
            1
        ),

        "overview": movie.get(
            "overview",
            "No description available."
        ),

        "poster": (
            IMAGE_BASE_URL + movie["poster_path"]
            if movie.get("poster_path")
            else None
        )
    }


# ---------------------------------------
# HOME PAGE
# ---------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# ---------------------------------------
# SEARCH MOVIES
# ---------------------------------------

@app.route("/api/search")
def search_movies():

    movie_name = request.args.get(
        "q",
        ""
    ).strip()

    if not movie_name:

        return jsonify({
            "error": "Please enter a movie name."
        }), 400

    data, error = tmdb_request(
        "/search/movie",
        {
            "query": movie_name,
            "language": "en-US",
            "page": 1,
            "include_adult": False
        }
    )

    if error:

        return jsonify({
            "error": error
        }), 500

    movies = []

    for movie in data.get(
        "results",
        []
    )[:10]:

        movies.append(
            clean_movie(movie)
        )

    return jsonify({
        "movies": movies
    })


# ---------------------------------------
# RECOMMENDATIONS
# ---------------------------------------

@app.route(
    "/api/recommendations/<int:movie_id>"
)
def get_recommendations(movie_id):

    recommended, error1 = tmdb_request(
        f"/movie/{movie_id}/recommendations",
        {
            "language": "en-US",
            "page": 1
        }
    )

    similar, error2 = tmdb_request(
        f"/movie/{movie_id}/similar",
        {
            "language": "en-US",
            "page": 1
        }
    )

    if error1 and error2:

        return jsonify({
            "error": error1
        }), 500

    movies = []

    if recommended:

        movies.extend(
            recommended.get(
                "results",
                []
            )
        )

    if similar:

        movies.extend(
            similar.get(
                "results",
                []
            )
        )

    # Remove duplicate movies
    unique_movies = {}

    for movie in movies:

        movie_id_value = movie.get("id")

        if movie_id_value:

            unique_movies[
                movie_id_value
            ] = movie

    movies = list(
        unique_movies.values()
    )

    # Sort by rating
    movies.sort(
        key=lambda movie:
        movie.get(
            "vote_average",
            0
        ) or 0,

        reverse=True
    )

    # Maximum 12 movies
    movies = movies[:12]

    return jsonify({
        "movies": [
            clean_movie(movie)
            for movie in movies
        ]
    })


# ---------------------------------------
# HEALTH CHECK
# ---------------------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "OK"
    })


# ---------------------------------------
# START SERVER
# ---------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )