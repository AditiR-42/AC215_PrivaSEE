#The third functionality of the privaSEE app is to recommend users services that score well in their particular domains of interest. Users may ask questions like "what's a service similar to X app but has a higher score"? Or, they can ask "if I'm looking for an app to do such and such, which app should I use?".

#In this script, we assume that we have a database of scored apps. We have service names and scores. We need to find a way to categorize apps based on more granular categories than just "social media" or "music". Ie we must take into account the size, functionality, etc. Then, we would layer an LLM on top of this so that users can converse.

import pandas as pd
import numpy as np
import json
from google.cloud import storage
import io
import os
import random
from google_play_scraper import app
from google_play_scraper import search
from fuzzywuzzy import fuzz
import re

print("Current Working Directory:", os.getcwd())
# Set the environment variable in Python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/ac215-privasee-datapipeline.json"
# Initialize the GCS client
storage_client = storage.Client()

# Define the bucket name and file path in the bucket
bucket_name = "legal-terms-data"
file_path = "tosdr-data/raw/intermediate_data_files/services_and_ratings.csv"

# Get the bucket and blob (file) from GCS
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_path)

# Download the content of the file as a string
data = blob.download_as_text()

# Read the data into a DataFrame
df = pd.read_csv(io.StringIO(data))

#drop the "Unnamed: 0" column
df = df.drop(columns=['Unnamed: 0'])
df = df.reset_index(drop=True)

# Function to get the best match from search using fuzzy matching
def get_best_app_details(service_name):
    try:
        # Perform a search and get multiple results
        search_results = search(service_name, lang="en", country="us", n_hits=5)
        
        # Initialize variables for the best match
        best_match = None
        highest_score = 0
        
        # Iterate through the search results and use fuzzy matching on titles
        for result in search_results:
            title = result.get('title', '')
            match_score = fuzz.ratio(service_name.lower(), title.lower())
            
            # Check if this result is the best match based on the score threshold
            if match_score > highest_score:
                highest_score = match_score
                best_match = result
                
                # If match score is above a threshold (e.g., 90), stop early
                if match_score >= 99:
                    break
        
        # If a match was found, return its details
        if best_match:
            return pd.Series({
                'AppID': best_match.get('appId'),
                'Title': best_match.get('title'),
                'Genre': best_match.get('genre'),
                'Score': best_match.get('score'),
                'Installs': best_match.get('installs')
            })
        
        # If no close match is found, return empty values
        return pd.Series({
            'AppID': None,
            'Title': None,
            'Genre': None,
            'Score': None,
            'Installs': None
        })
    except Exception as e:
        print(f"Error searching for {service_name}: {e}")
        return pd.Series({
            'AppID': None,
            'Title': None,
            'Genre': None,
            'Score': None,
            'Installs': None
        })

# Apply the function to each row in 'Service' and expand to multiple columns
df_try2 = df.join(df['Service'].apply(get_best_app_details))

# Function to clean and normalize strings by removing punctuation, extra spaces, and converting to lowercase
def clean_string(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', s)).strip().lower()

# Function to check if Service is a subset of Title
def is_subset_match(service, title):
    if pd.isna(service) or pd.isna(title):
        return False  # Return False if either value is NaN
    clean_service = clean_string(service)
    clean_title = clean_string(title)
    return clean_service in clean_title

# Apply the function to create a new column 'CloseMatch'
df_try2['CloseMatch'] = df_try2.apply(lambda row: is_subset_match(row['Service'], row['Title']), axis=1)

# Separate into two DataFrames based on the 'CloseMatch' column
df_close_matches = df_try2[df_try2['CloseMatch']].drop(columns=['CloseMatch'])

#for each row in df_close_matches, use the AppID to get info that's useful but we don't yet have

# Function to get additional app details that are not already in the DataFrame
def get_additional_app_details(app_id):
    try:
        # Retrieve detailed information using the app id
        details = app(app_id, lang="en", country="us")
        return pd.Series({
            'Description': details.get('description'),
            'Price': details.get('price'),
            'Developer': details.get('developer'),
            'Content Rating': details.get('contentRating'),
            'App URL': details.get('url'),
            'Updated Date': details.get('updated'),
            'Ratings': details.get('ratings'),
            'Reviews': details.get('reviews'),
            'Free': details.get('free'),
            'Contains Ads': details.get('containsAds')
        })
    except Exception as e:
        print(f"Error retrieving details for app ID {app_id}: {e}")
        return pd.Series({
            'Description': None,
            'Price': None,
            'Developer': None,
            'Content Rating': None,
            'App URL': None,
            'Updated Date': None,
            'Ratings': None,
            'Reviews': None,
            'Free': None,
            'Contains Ads': None
        })

# Apply the function to each AppID in df_close_matches and expand to multiple columns
df_detailed_close_matches = df_close_matches.join(df_close_matches['AppID'].apply(get_additional_app_details))

# Convert the DataFrame to a CSV string in memory
csv_buffer = io.StringIO()
df_detailed_close_matches.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

# Define the output path in the bucket
output_file_path = "tosdr-data/raw/data_for_recommendations.csv"  # Adjust this path as needed

# Upload the CSV data to GCS
output_blob = bucket.blob(output_file_path)
output_blob.upload_from_string(csv_data, content_type="text/csv")

print(f"Data successfully saved to gs://{bucket_name}/{output_file_path}")