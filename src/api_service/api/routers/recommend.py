from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from google.cloud import storage, aiplatform
from vertexai.generative_models import GenerativeModel
import pandas as pd
from io import StringIO
import json
from fuzzywuzzy import process
from nltk.corpus import wordnet
import nltk
import os
import traceback

nltk.download("wordnet")

# Initialize FastAPI and Router
router = APIRouter()

# Initialize dataset as a global placeholder
df = None
formatted_data = None

# Initialize Vertex AI
aiplatform.init(project="ac215-privasee", location="us-central1")

# Initialize the model
model = GenerativeModel("gemini-1.5-flash-002")


# Function to load dataset
def load_dataset():
    try:
        client = storage.Client()
        bucket_name = "legal-terms-data"
        file_path = "tosdr-data/clean/clean_data_for_recs.csv"
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        data = blob.download_as_text()
        df = pd.read_csv(StringIO(data))
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")


# Function to initialize dataset lazily
def initialize_dataset():
    global df, formatted_data
    if df is None:
        try:
            df = load_dataset()
            formatted_data = df["formatted"].tolist()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error initializing dataset: {str(e)}")


# Request Model
class QueryRequest(BaseModel):
    query: str


# Helper Functions
def extract_service_and_requirements(query: str):
    prompt = (
        f"Analyze this query: '{query}'. Extract values for the following fields if mentioned, otherwise return 'NA':\n"
        f"- Service: Name of the service (e.g., Facebook, Instagram)\n"
        f"- privacy_rating: A letter grade (A, B, C, D, or 'No rating yet')\n"
        f"- Title: Alternative name for the service\n"
        f"- Genre: The app's genre (e.g., social media, music streaming)\n"
        f"- app_score: App store score (numeric value, e.g., 4.5)\n"
        f"- Installs: Number of installs (numeric value, e.g., 5000000)\n"
        f"- Content Rating: e.g., Everyone, Teen\n"
        f"- num_ratings: Minimum number of ratings (numeric value)\n"
        f"- num_reviews: Minimum number of reviews (numeric value)\n"
        f"- Free: True or False\n"
        f"- Contains Ads: True or False\n\n"
        f"Respond in valid JSON format with the fields as keys. Use 'NA' for any field not mentioned in the query."
    )

    response = model.generate_content(prompt)

    try:
        clean_response = response.text.strip().strip("```").strip("json").strip()
        parsed_data = json.loads(clean_response)

        expected_fields = [
            "Service",
            "privacy_rating",
            "Title",
            "Genre",
            "app_score",
            "Installs",
            "Content Rating",
            "num_ratings",
            "num_reviews",
            "Free",
            "Contains Ads",
        ]
        return {field: parsed_data.get(field, "NA") for field in expected_fields}

    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON response: {e}")

def filter_dataframe(criteria):
    """
    Filters a DataFrame based on criteria extracted from the query.

    Args:
        criteria (dict): The extracted values from the query.

    Returns:
        pd.DataFrame: A filtered DataFrame based on the criteria.
    """
    initialize_dataset()  # Ensure the dataset is loaded
    filtered_df = df.copy()
    # Define a mapping for privacy ratings
    privacy_rating_order = {
        "A": 4,
        "B": 3,
        "C": 2,
        "D": 1,
        "No rating yet": 0,  # Lowest rating for unassigned or missing values
        None: 0  # Treat missing ratings as the lowest
    }

    def get_rating_value(rating):
        return privacy_rating_order.get(rating, 0)

    def find_best_genre_match_with_gemini(user_genre, genres_in_df):
        """
        Use Gemini to find the best-matching genre based on meaning.

        Args:
            user_genre (str): The genre provided by the user or extracted from the service.
            genres_in_df (list): List of unique genres in the DataFrame.

        Returns:
            str: The best-matching genre, or None if no suitable match is found.
        """
        # Create a prompt for Gemini
        prompt = (
            f"The user provided the genre '{user_genre}'. "
            f"Here is a list of genres from the dataset: {genres_in_df}. "
            f"Identify the genre from the dataset that best matches the user's input. "
            f"Return only the best matching genre as a plain text string."
        )

        # Generate response from Gemini
        response = model.generate_content(prompt)
        best_genre_match = response.text.strip()
        best_genre_match = best_genre_match.lower()

        # Ensure the response is valid and in the list of genres
        if best_genre_match in genres_in_df:
            return best_genre_match
        else:
            print("Gemini did not return a valid match.")
            return None

    filtered_df = df.copy()

    # Handle 'Service' criterion separately to update criteria
    if criteria.get("Service") != "NA" and criteria.get("Service") is not None:
        # Create an intermediate DataFrame filtered for the specific service
        service_df = filtered_df[filtered_df["Service"].str.contains(criteria["Service"], case=False, na=False)]

        if not service_df.empty:
            # Extract Genre and privacy_rating for the specified service
            extracted_genre = service_df.iloc[0]["Genre"]
            extracted_privacy_rating = service_df.iloc[0]["privacy_rating"]

            # Update criteria with extracted Genre and privacy_rating
            if extracted_genre:
                criteria["Genre"] = extracted_genre
            if extracted_privacy_rating:
                criteria["privacy_rating"] = extracted_privacy_rating

    # Determine the best-matching genre (AFTER service-based genre extraction)
    if "Genre" in criteria and criteria["Genre"] != "NA" and criteria["Genre"] is not None:
        user_genre = criteria["Genre"]
        unique_genres = filtered_df["Genre"].dropna().unique().tolist()  # Get unique genres in the DataFrame
        best_genre_match = find_best_genre_match_with_gemini(user_genre, unique_genres)

        if best_genre_match:
            criteria["Genre"] = best_genre_match  # Update the genre in the criteria with the best match
        else:
            print("No sufficiently good match found for the Genre.")

    # Apply filters based on updated criteria
    for key, value in criteria.items():
        if value == "NA" or value is None:
            continue  # Skip criteria that are not specified

        if key == "Genre":
            # Filter by the best-matching genre
            filtered_df = filtered_df[filtered_df["Genre"] == value]

        elif key == "privacy_rating":
            # Filter for privacy ratings that are >= the specified value
            min_rating_value = get_rating_value(value)
            print(f"Filtering by Privacy Rating >= {value} (Rating Value: {min_rating_value})")
            filtered_df["rating_value"] = filtered_df["privacy_rating"].apply(get_rating_value)
            filtered_df = filtered_df[filtered_df["rating_value"] >= min_rating_value]
            filtered_df.drop(columns=["rating_value"], inplace=True)

        elif key == "Content Rating":
            # Exact match for content rating
            print(f"Filtering by Content Rating: {value}")
            filtered_df = filtered_df[filtered_df["Content Rating"] == value]

        elif key == "app_score":
            # Numeric filtering for app store score
            print(f"Filtering by App Score >= {value}")
            filtered_df = filtered_df[filtered_df["app_score"] >= float(value)]

        elif key == "Installs":
            # Numeric filtering for installs
            print(f"Filtering by Installs >= {value}")
            filtered_df = filtered_df[filtered_df["Installs"] >= int(value)]

        elif key == "num_ratings":
            # Numeric filtering for number of ratings
            print(f"Filtering by Number of Ratings >= {value}")
            filtered_df = filtered_df[filtered_df["num_ratings"] >= int(value)]

        elif key == "num_reviews":
            # Numeric filtering for number of reviews
            print(f"Filtering by Number of Reviews >= {value}")
            filtered_df = filtered_df[filtered_df["num_reviews"] >= int(value)]

        elif key == "Free":
            # Exact match for free apps
            print(f"Filtering by Free: {value}")
            filtered_df = filtered_df[filtered_df["Free"] == (value == "True")]

        elif key == "Contains Ads":
            # Exact match for ads
            print(f"Filtering by Contains Ads: {value}")
            filtered_df = filtered_df[filtered_df["Contains Ads"] == (value == "True")]

    # Filter out rows where privacy_rating is NaN
    filtered_df = filtered_df[pd.notna(filtered_df["privacy_rating"])]

    return filtered_df

def get_top_recommendation(filtered_df):
    """
    Sorts the filtered DataFrame by privacy rating (descending) and a weighted app score
    that considers both app_score and num_ratings. Returns the top row as the recommendation.

    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame that meets the user's requirements.

    Returns:
        pd.Series: The top row of the sorted DataFrame, representing the recommendation.
    """
    # Define the privacy rating order for sorting
    privacy_rating_order = {"A": 4, "B": 3, "C": 2, "D": 1, "No rating yet": 0}

    # Calculate the average app score across all rows (C) and a threshold (M)
    C = filtered_df["app_score"].mean() if not filtered_df["app_score"].empty else 0
    M = 100  # Assume a threshold of 100 ratings for balancing

    # Add a numeric column for privacy rating values
    filtered_df["rating_value"] = filtered_df["privacy_rating"].map(privacy_rating_order).fillna(0)

    # Calculate the weighted score (S_w)
    filtered_df["weighted_score"] = (
        (filtered_df["app_score"] * filtered_df["num_ratings"] + C * M) /
        (filtered_df["num_ratings"] + M)
    )

    # Sort by privacy rating (descending) and weighted score (descending)
    sorted_df = filtered_df.sort_values(by=["rating_value", "weighted_score"], ascending=[False, False])

    # Return the top row as the recommendation
    if not sorted_df.empty:
        return sorted_df.iloc[0]
    else:
        return None  # No recommendation if the DataFrame is empty

def generate_conversational_response(rec, user_query):
    """
    Uses Gemini to generate a conversational response based on the recommendation.

    Args:
        rec (pd.Series): The recommendation row from the filtered DataFrame.
        user_query (str): The original user query for context.

    Returns:
        str: A conversational response generated by Gemini.
    """
    # Extract basic information from the recommendation
    app_name = rec["Service"]
    privacy_rating = rec["privacy_rating"]
    genre = rec.get("Genre", "unspecified")
    app_score = rec.get("app_score", None)
    num_ratings = rec.get("num_ratings", None)
    description = rec.get("recommendation", "No description available.")
    installs = rec.get("Installs", None)

    # Construct a summary of the app
    app_summary = f"The app {app_name} has a privacy rating of {privacy_rating}."
    if app_score and num_ratings:
        app_summary += f" It has a user score of {app_score}, based on {num_ratings} ratings."
    if installs:
        app_summary += f" The app has been installed over {installs} times."
    app_summary += f" Here's a bit about it: {description}"

    # Gemini prompt to generate a conversational response
    prompt = (
        f"You are an app recommendation assistant. A user asked: '{user_query}'.\n\n"
        f"Based on their preferences, you recommend the app '{app_name}'. "
        f"The app has a privacy rating of '{privacy_rating}'."
    )
    prompt += f" {app_summary}\n\n"
    prompt += (
        "Respond to the user conversationally, providing this information in a friendly and engaging way. "
        "Focus on the privacy rating but also mention relevant details like installs and ratings to make your response helpful. "
        "Do not include unnecessary details, but make the user feel confident about the recommendation."
    )

    # Generate the response using Gemini
    response = model.generate_content(prompt)
    return response.text.strip()

# function for the whole process
def provide_a_rec(query):
    
    #step 1: extract criteria from query
    criteria = extract_service_and_requirements(query)
    
    #step 2: filter dataframe and keep only apps meeting all minimum requirements
    filtered_df = filter_dataframe(criteria)
    
    #step 3: get top recommendation
    rec = get_top_recommendation(filtered_df)
    
    #step 4: get conversational response
    conversational_response = generate_conversational_response(rec, query)
    
    return conversational_response

# API Endpoints
@router.post("/recommend")
def recommend_app(request: QueryRequest):
    query = request.query
    try:
        # Use the new function to provide a recommendation
        conversational_response = provide_a_rec(query)

        # Return the response as a JSON object
        return {"recommendation": conversational_response}
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        