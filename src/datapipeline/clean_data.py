import pandas as pd
import re
from bs4 import BeautifulSoup
from google.cloud import storage
import os
import io

print("Current Working Directory:", os.getcwd())
# Set the environment variable in Python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../../../secrets/ac215-privasee-datapipeline.json"
# Initialize the GCS client
storage_client = storage.Client()
def upload_df_to_gcs(bucket_name, df, destination_blob_name):
    """Uploads a DataFrame as a CSV to GCS directly from memory."""
    # Convert DataFrame to CSV string
    csv_data = df.to_csv(index=False)

    # Get the bucket and blob objects
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload the CSV string to GCS
    blob.upload_from_string(csv_data, content_type='text/csv')

    print(f"Uploaded DataFrame to {destination_blob_name} in bucket {bucket_name}.")

def read_csv_from_gcs(bucket_name, source_blob_name):
    """Read a CSV file from GCS into a DataFrame."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    # Download the CSV content as text (UTF-8)
    content = blob.download_as_text()
    # Read it directly into a DataFrame
    return pd.read_csv(io.StringIO(content))


# Funtions to clean the data
def remove_html_tags(text):
    """Remove HTML tags using BeautifulSoup."""
    soup = BeautifulSoup(text, "html.parser")
    cleaned_text = soup.get_text()
    return cleaned_text
def remove_text_in_brackets(text):
    """Remove text within angle brackets."""
    return re.sub(r'<[^>]*>', '', text)

def remove_urls_and_emails(text):
    """Remove URLs and email addresses."""
    #remove urls
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove emails
    text = re.sub(r'\S*@\S*\s?', '', text)
    return text

def remove_control_characters(text):
    """Remove non-printable and control characters."""
    # Replace common control characters with space
    text = re.sub(r'[\r\n\t\f\v]', ' ', text)
    # Remove remaining control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return text

def remove_special_characters(text, remove_digits=False):
    """Remove special characters, optionally including digits."""
    pattern = r'[^a-zA-Z0-9\s]' if not remove_digits else r'[^a-zA-Z\s]'
    text = re.sub(pattern, '', text)
    return text

def remove_text_in_parentheses(text):
    """Remove text within angle brackets."""
    return re.sub(r'\s*\([^)]*\)', '', text).strip()

def preprocess_text(text):
    """Apply all preprocessing steps to the text."""
    text = remove_text_in_brackets(text)
    text = remove_urls_and_emails(text)
    text = remove_control_characters(text)
    text = remove_special_characters(text)
    test= remove_text_in_parentheses(text)
    return text


def main():
    # List all buckets in your project to confirm the client works
    buckets = list(storage_client.list_buckets())
    for bucket in buckets:
        print(bucket.name)

    bucket_name = 'legal-terms-data'
    source_blob_name = 'tosdr-data/clean/final_output2.csv'
    destination_blob_name = 'tosdr-data/clean/cleaned_output2.csv'
    # Read the CSV from GCS
    # Read the CSV from GCS
    df = read_csv_from_gcs(bucket_name, source_blob_name)
    print(df.shape)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    df.head()
    # Identify services where we have no texts
    no_text = df.groupby('service')['document_text_shortened'].apply(lambda x: x.isna().any()).reset_index()
    no_text.document_text_shortened.value_counts()
    print("shape of df: ", df.shape)
    # drop the nulls
    new_df = df.dropna(subset=["document_text_shortened"], how='any').reset_index()
    print("Info about new df after dropping observations with no t&cs: ")
    print(new_df.info())
    ### Apply data cleaning
    new_df["full_text_clean"] = new_df["document_text_shortened"].apply(preprocess_text)
    new_df["privacy_issue_clean"] = new_df["case"].apply(preprocess_text)
    new_df["support_text_clean"] = new_df["title"].apply(preprocess_text)
    # Rename some columns
    new_df = new_df.rename(columns={'case': 'privacy_issue',
                                    'topic': 'parent_privacy_issue',
                                    'status': 'review_status'
                                    })
    print("cleaned_df: ", new_df.heead(2))

    #upload cleaned df to gcs
    upload_df_to_gcs(bucket_name=bucket_name, df=new_df,
                     destination_blob_name=destination_blob_name)

if __name__ == "__main__":
    main()