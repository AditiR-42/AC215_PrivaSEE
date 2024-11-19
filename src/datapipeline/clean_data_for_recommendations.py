# in this script, we load in the raw data for recommendations, clean it, and put it back into gcs

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
file_path = "tosdr-data/raw/data_for_recommendations.csv"

# Get the bucket and blob (file) from GCS
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_path)

# Download the content of the file as a string
data = blob.download_as_text()

# Read the data into a DataFrame
df = pd.read_csv(io.StringIO(data))

#delete unnecessary columns
df.drop(['AppID', 'Price', 'App URL', 'Updated Date'], axis=1, inplace=True)

# Standardize the 'genre' column (lowercase)
df["Genre"] = df["Genre"].str.lower()

#rename things for clarity
df.rename(columns={'Rating': 'privacy_rating'}, inplace=True)
df.rename(columns={'Score': 'app_score'}, inplace=True)
df.rename(columns={'Ratings': 'num_ratings'}, inplace=True)
df.rename(columns={'Reviews': 'num_reviews'}, inplace=True)

# Ensure 'score' is numeric
df["app_score"] = pd.to_numeric(df["app_score"], errors="coerce")

#make formatting column for conversion later
df['formatted'] = (
    "Service: " + df['Service'] +
    "; Title: " + df['Title'] +
    "; Privacy Rating: " + df['privacy_rating'] +
    "; App Score: " + df['app_score'].astype(str) +
    "; Category: " + df['Genre'] +
    "; Free: " + df['Free'].astype(str) +
    "; Number of Ratings: " + df['num_ratings'].astype(str) +
    "; Number of Reviews: " + df['num_reviews'].astype(str) +
    "; Description: " + df['Description']
)

# Convert the DataFrame to a CSV string in memory
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

# Define the output path in the bucket
output_file_path = "tosdr-data/clean/clean_data_for_recs.csv"  # Adjust this path as needed

# Upload the CSV data to GCS
output_blob = bucket.blob(output_file_path)
output_blob.upload_from_string(csv_data, content_type="text/csv")

print(f"Data successfully saved to gs://{bucket_name}/{output_file_path}")