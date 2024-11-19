from google.cloud import storage
import pandas as pd
from io import StringIO
from google.cloud import aiplatform

# Initialize GCS client
client = storage.Client()

# Define bucket and file path
bucket_name = 'legal-terms-data'
file_path = 'tosdr-data/clean/clean_data_for_recs.csv'
bucket = client.bucket(bucket_name)
blob = bucket.blob(file_path)

# Download the file content as a string
data = blob.download_as_text()

# Load the CSV data into a pandas DataFrame
df = pd.read_csv(StringIO(data))

# Convert the dataset to a list of strings
formatted_data = df['formatted'].tolist()

from vertexai.generative_models import GenerativeModel
import json

# Initialize AI Platform
aiplatform.init(project="ac215-privasee", location="us-central1")

# Function to extract service and requirements
def extract_service_and_requirements(query):
    prompt = (
        f"Analyze this query: '{query}'. Identify the target service (e.g., an app or platform name) OR the genre (e.g., 'social media'), "
        f"and any 'must-have' features (e.g., 'no ads', 'high privacy', 'more than X number of reviews'). Respond ONLY in valid JSON format with the keys "
        f"'target_service', 'genre', and 'must_haves', e.g., {{'target_service': 'Facebook', 'genre': 'social media', 'must_haves': ['no ads', 'high privacy']}}."
    )
    model = GenerativeModel("gemini-1.5-flash-002")
    response = model.generate_content(prompt)
    
    try:
        # Clean and parse the response
        clean_response = response.text.strip().strip("```").strip("json").strip()
        parsed_data = json.loads(clean_response)
        return (
            parsed_data.get("target_service"),
            parsed_data.get("genre"),
            parsed_data.get("must_haves", [])
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON response: {e}")

# Extract the target app's privacy rating from df
def get_target_app_privacy_rating(target_service=None, genre=None):
    # Define the hierarchy for privacy ratings
    privacy_rating_order = {
        "A": 4,
        "B": 3,
        "C": 2,
        "D": 1,
        "No rating yet": 0
    }
    
    def get_rating_value(rating):
        # Return the numeric value for the rating, default to 0 for invalid/missing ratings
        return privacy_rating_order.get(rating, 0)
    
    if target_service:
        matched_row = df[df['Service'].str.contains(target_service, case=False, na=False)]
        #print("Matched Row for Target Service:", matched_row)
        if not matched_row.empty:
            # Extract the privacy rating and convert it to a numeric value
            return get_rating_value(matched_row.iloc[0]['privacy_rating'])
    
    if genre:
        #print("Unique Genres in Dataset:", df['Genre'].unique())
        genre_rows = df[df['Genre'].str.contains(genre, case=False, na=False)]
        #print("Matched Rows for Genre:", genre_rows)
        
        if not genre_rows.empty:
            # Apply the hierarchy manually to find the maximum rating
            genre_rows['rating_value'] = genre_rows['privacy_rating'].apply(get_rating_value)
            return genre_rows['rating_value'].max()  # Now numeric comparison will work
        
    raise ValueError("Neither target service nor genre could be matched in the dataset.")

# Function to recommend an app
def recommend_app_with_gemini(target_service, must_haves, formatted_data, target_app_privacy_rating):
    # Define the privacy rating hierarchy in the prompt
    privacy_rating_hierarchy = (
        "Privacy ratings are ranked as follows: 'A' is the highest privacy rating, followed by 'B', 'C', and 'D'. "
        "'No rating yet' is treated as the lowest privacy rating."
    )
    
    # Create the recommendation prompt
    prompt = (
        f"Given the following dataset of apps:\n{formatted_data}\n\n"
        f"The user is looking for an app like '{target_service}' with the following requirements: {must_haves}.\n"
        f"Find an app in the same category as '{target_service}' that meets these requirements and has a privacy rating "
        f"higher than '{target_app_privacy_rating}' (or equal if it's already the highest in the dataset).\n"
        f"{privacy_rating_hierarchy}\n"
        f"Additionally, prioritize apps with a high score, a high number of ratings, and a strong reputation.\n"
        f"Respond with details about the recommended app in JSON format, including keys: 'Service', 'Title', 'Privacy Rating', "
        f"'Score', 'Category', 'Description'."
    )
    model = GenerativeModel("gemini-1.5-flash-002")
    response = model.generate_content(prompt)
    
    try:
        # Clean and parse the response
        clean_response = response.text.strip().strip("```").strip("json").strip()
        recommendation = json.loads(clean_response)
        return recommendation
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON response: {e}")

# Function to generate a conversational response
def generate_conversational_response(recommendation):
    # Extract details from the recommendation for the prompt
    service = recommendation.get("Service", "Unknown Service")
    title = recommendation.get("Title", "Unknown Title")
    privacy_rating = recommendation.get("Privacy Rating", "Unknown Privacy Rating")
    score = recommendation.get("Score", "Unknown Score")
    category = recommendation.get("Category", "Unknown Category")
    description = recommendation.get("Description", "")

    # Create a summary of the app description
    summary_prompt = (
        f"Summarize the following app description in 1-2 sentences:\n\n{description}\n\n"
        f"Respond with a concise summary."
    )
    model = GenerativeModel("gemini-1.5-flash-002")
    summary_response = model.generate_content(summary_prompt)
    summary = summary_response.text.strip()

    # Create the conversational recommendation prompt
    conversational_prompt = (
        f"Based on the user's preferences, generate a conversational recommendation for the following app details:\n\n"
        f"Service: {service}\nTitle: {title}\nPrivacy Rating: {privacy_rating}\nScore: {score}\n"
        f"Category: {category}\nSummary: {summary}\n\n"
        f"Respond with a conversational paragraph."
    )
    conversational_response = model.generate_content(conversational_prompt)
    return conversational_response.text.strip()

### Example Queries

#type 1: query gives a genre
query = "Give me a recommendation for the genre shopping with a good privacy score."

# Step 1: Extract details from the query
try:
    target_service, genre, must_haves = extract_service_and_requirements(query)
    #print("Extracted Target Service:", target_service)  # Debugging
    #print("Extracted Genre:", genre)  # Debugging
    #print("Must-Haves:", must_haves)  # Debugging
except ValueError as e:
    #print(f"Error extracting query details: {e}")
    target_service, genre, must_haves = None, None, []

# Step 2: Get the target app's privacy rating
try:
    target_app_privacy_rating = get_target_app_privacy_rating(target_service, genre)
    #print("Target App Privacy Rating:", target_app_privacy_rating)  # Debugging
except ValueError as e:
    #print(f"Error: {e}")
    target_app_privacy_rating = "Low"  # Fallback value if neither service nor genre is matched

# Step 3: Recommend an app
recommendation = recommend_app_with_gemini(
    target_service or genre,  # Use the genre if the service is not specified
    must_haves,
    formatted_data,
    target_app_privacy_rating
)

# Step 4: Generate a conversational response
if recommendation:
    conversational_output = generate_conversational_response(recommendation)
    print("Conversational Recommendation:")
    print(conversational_output)
else:
    print("No suitable app could be recommended based on the provided query.")

#type 2: query gives an app
query = "I want an app like Signal with a good privacy score."

# Step 1: Extract details from the query
try:
    target_service, genre, must_haves = extract_service_and_requirements(query)
    #print("Extracted Target Service:", target_service)  # Debugging
    #print("Extracted Genre:", genre)  # Debugging
    #print("Must-Haves:", must_haves)  # Debugging
except ValueError as e:
    #print(f"Error extracting query details: {e}")
    target_service, genre, must_haves = None, None, []

# Step 2: Get the target app's privacy rating
try:
    target_app_privacy_rating = get_target_app_privacy_rating(target_service, genre)
    #print("Target App Privacy Rating:", target_app_privacy_rating)  # Debugging
except ValueError as e:
    #print(f"Error: {e}")
    target_app_privacy_rating = "Low"  # Fallback value if neither service nor genre is matched

# Step 3: Recommend an app
recommendation = recommend_app_with_gemini(
    target_service or genre,  # Use the genre if the service is not specified
    must_haves,
    formatted_data,
    target_app_privacy_rating
)

# Step 4: Generate a conversational response
if recommendation:
    conversational_output = generate_conversational_response(recommendation)
    print("Conversational Recommendation:")
    print(conversational_output)
else:
    print("No suitable app could be recommended based on the provided query.")