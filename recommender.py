import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Load the movie dataset
movies = pd.read_csv("data/movies.csv")


# Replace missing values with empty strings
movies = movies.fillna("")


# Combine important movie information
movies["combined_features"] = (
    movies["genre"] + " "
    + movies["keywords"] + " "
    + movies["cast"] + " "
    + movies["director"] + " "
    + movies["overview"]
)


# Convert text into numerical TF-IDF vectors
vectorizer = TfidfVectorizer(stop_words="english")

feature_matrix = vectorizer.fit_transform(movies["combined_features"])


# Calculate similarity between all movies
similarity_matrix = cosine_similarity(feature_matrix)


def recommend_movies(movie_title, number_of_recommendations=5):
    """
    Return movies similar to the selected movie.
    """

    # Find the selected movie
    matching_movies = movies[
        movies["title"].str.lower() == movie_title.lower()
    ]

    if matching_movies.empty:
        return []

    movie_index = matching_movies.index[0]

    # Get similarity scores for the selected movie
    similarity_scores = list(
        enumerate(similarity_matrix[movie_index])
    )

    # Sort from most similar to least similar
    similarity_scores = sorted(
        similarity_scores,
        key=lambda x: x[1],
        reverse=True
    )

    # Remove the selected movie itself
    similarity_scores = [
        item for item in similarity_scores
        if item[0] != movie_index
    ]

    # Select the requested number of recommendations
    top_movies = similarity_scores[:number_of_recommendations]

    recommendations = []

    for index, score in top_movies:
        recommendations.append({
            "title": movies.iloc[index]["title"],
            "genre": movies.iloc[index]["genre"],
            "director": movies.iloc[index]["director"],
            "score": round(float(score) * 100, 2)
        })

    return recommendations


# Test the recommendation system
if __name__ == "__main__":

    movie = "The Dark Knight"

    recommendations = recommend_movies(movie, 5)

    print("\nRecommended Movies:")
    print("-------------------")

    for movie in recommendations:
        print(
            f"{movie['title']} "
            f"- Similarity: {movie['score']}%"
        )