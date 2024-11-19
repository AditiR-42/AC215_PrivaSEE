from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from google.cloud import storage, aiplatform
from vertexai.generative_models import GenerativeModel
import pandas as pd
from io import StringIO
import json

# Initialize FastAPI and Router
router = APIRouter()

# Load Dataset Function (Lazy Loading)
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

# Initialize Vertex AI
aiplatform.init(project="ac215-privasee", location="us-central1")

# Request Model
class QueryRequest(BaseModel):
    query: str

# Helper Functions
def extract_service_and_requirements(query: str):
    prompt = (
        f"Analyze this query: '{query}'. Identify the target service (e.g., an app or platform name) OR the genre (e.g., 'social media'), "
        f"and any 'must-have' features (e.g., 'no ads', 'high privacy', 'more than X number of reviews'). Respond ONLY in valid JSON format with the keys "
        f"'target_service', 'genre', and 'must_haves'."
    )
    model = GenerativeModel("gemini-1.5-flash-002")
    response = model.generate_content(prompt)

    try:
        clean_response = response.text.strip().strip("```").strip("json").strip()
        parsed_data = json.loads(clean_response)
        return parsed_data.get("target_service"), parsed_data.get("genre"), parsed_data.get("must_haves", [])
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding JSON response: {e}")

def get_target_app_privacy_rating(df, target_service=None, genre=None):
    privacy_rating_order = {"A": 4, "B": 3, "C": 2, "D": 1, "No rating yet": 0}

    def get_rating_value(rating):
        return privacy_rating_order.get(rating, 0)

    if target_service:
        matched_row = df[df["Service"].str.contains(target_service, case=False, na=False)]
        if not matched_row.empty:
            return get_rating_value(matched_row.iloc[0]["privacy_rating"])

    if genre:
        genre_rows = df[df["Genre"].str.contains(genre, case=False, na=False)]
        if not genre_rows.empty:
            genre_rows["rating_value"] = genre_rows["privacy_rating"].apply(get_rating_value)
            return genre_rows["rating_value"].max()

    return 0

def recommend_app_with_gemini(target_service, must_haves, formatted_data, target_app_privacy_rating):
    privacy_rating_hierarchy = (
        "Privacy ratings are ranked as follows: 'A' is the highest privacy rating, followed by 'B', 'C', and 'D'. "
        "'No rating yet' is treated as the lowest privacy rating."
    )
    prompt = (
        f"Given the following dataset of apps:\n{formatted_data}\n\n"
        f"The user is looking for an app like '{target_service}' with the following requirements: {must_haves}.\n"
        f"Find an app in the same category as '{target_service}' that meets these requirements and has a privacy rating "
        f"higher than '{target_app_privacy_rating}'.\n"
        f"{privacy_rating_hierarchy}\n"
        f"Respond with details about the recommended app in JSON format."
    )
    model = GenerativeModel("gemini-1.5-flash-002")
    response = model.generate_content(prompt)

    try:
        clean_response = response.text.strip().strip("```").strip("json").strip()
        recommendation = json.loads(clean_response)
        return recommendation
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding JSON response: {e}")

# API Endpoints
@router.post("/recommend")
def recommend_app(request: QueryRequest):
    query = request.query
    try:
        # Load dataset
        df = load_dataset()
        formatted_data = df["formatted"].tolist()

        # Extract details from query
        target_service, genre, must_haves = extract_service_and_requirements(query)

        # Get privacy rating
        target_app_privacy_rating = get_target_app_privacy_rating(df, target_service, genre)

        # Generate recommendation
        recommendation = recommend_app_with_gemini(
            target_service or genre, must_haves, formatted_data, target_app_privacy_rating
        )
        return {"recommendation": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
