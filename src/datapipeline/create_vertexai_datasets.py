import pandas as pd
import json
from google.cloud import storage
from sklearn.model_selection import train_test_split
import io
import os

print("Current Working Directory:", os.getcwd())
# Set the environment variable in Python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../../../secrets/ac215-privasee-datapipeline.json"
# Initialize the GCS client
storage_client = storage.Client()


# Read CSV from GCS bucket
def read_csv_from_gcs(bucket_name, source_blob_name):
    """Read a CSV file from GCS into a DataFrame."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    # Download the CSV content as text (UTF-8)
    content = blob.download_as_text()
    # Read it directly into a DataFrame
    return pd.read_csv(io.StringIO(content))

# Group issues by service name and full text
def group_df_by_issues(df):
    """Group issues by service name and full text, aggregating issues into lists."""
    grouped_df = (
        df.groupby(["service", "full_text_clean"])["privacy_issue"]
        .apply(list)  # Collect issues into a list
        .reset_index()
    )
    return grouped_df

def return_all_labels(df):
    """takes in df and returns all unique privacy issues"""
    return list(df.privacy_issue.unique())

# Convert grouped data to JSONL-ready format for verexAI
def convert_to_jsonl(df, all_labels, ml_use):
    """Convert grouped data into JSONL format for multi-label classification."""
    jsonl_data = []
    for _, row in df.iterrows():
        classification_annotations = [
            {"displayName": label} for label in row["privacy_issue"]
        ]
        jsonl_entry = {
            "classificationAnnotations": classification_annotations,
            "textContent": row["full_text_clean"],  # or "textGcsUri" if text is in GCS
            "dataItemResourceLabels": {
                "aiplatform.googleapis.com/ml_use": ml_use
            }
        }
        jsonl_data.append(jsonl_entry)
    return jsonl_data


# Save the JSONL data to a file
def save_to_jsonl(data, file_name):
    """Save a list of dictionaries to a JSONL file."""
    with open(file_name, "w") as f:
        for entry in data:
            json.dump(entry, f)
            f.write("\n")
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Upload a file to GCS."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"Uploaded {source_file_name} to {destination_blob_name}")

def main():
    # GCS parameters
    bucket_name = 'legal-terms-data'
    source_blob_name = 'tosdr-data/clean/df_mod_v1.csv'
    train_destination_blob_name = 'tosdr-data/modeling/train/train.jsonl'
    val_destination_blob_name = 'tosdr-data/modeling/val/val.jsonl'
    test_destination_blob_name = 'tosdr-data/modeling/test/test.jsonl'

    # Read the CSV from GCS
    df = read_csv_from_gcs(bucket_name, source_blob_name)

    print("finished reading in data")
    # Define all possible labels
    ALL_LABELS = return_all_labels(df)

    print("finished getting all the labels")

    # Group issues by service name and full text
    grouped_df = group_df_by_issues(df)

    print("finished grouping the data by service and privacy issue")

    # Split into train (80%), validation (10%), and test (10%)
    train_data, temp_data = train_test_split(grouped_df, test_size=0.3, random_state=42)
    val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)
    print("Train, val, test shapes in df:", train_data.shape, val_data.shape, test_data.shape)
    print("finished train/val/test/split")
    train_jsonl = convert_to_jsonl(df=train_data, all_labels=ALL_LABELS, ml_use="training")
    val_jsonl = convert_to_jsonl(df=val_data, all_labels=ALL_LABELS, ml_use="validation")
    test_jsonl = convert_to_jsonl(df=test_data, all_labels=ALL_LABELS, ml_use="testing")
    print("Train, val, test shapes in jsnol form:", len(train_jsonl), len(val_jsonl), len(test_jsonl))
    # Save the splits to JSONL files
    save_to_jsonl(train_jsonl, "train.jsonl")
    save_to_jsonl(val_jsonl, "val.jsonl")
    save_to_jsonl(test_jsonl, "test.jsonl")
    print("finished saving train/val/test split to jsonl")

    # Upload JSONL files to GCS
    upload_to_gcs(bucket_name=bucket_name, source_file_name="train.jsonl",
                  destination_blob_name=train_destination_blob_name)
    upload_to_gcs(bucket_name=bucket_name, source_file_name="val.jsonl",
                  destination_blob_name=val_destination_blob_name)
    upload_to_gcs(bucket_name=bucket_name, source_file_name="test.jsonl",
                  destination_blob_name=test_destination_blob_name)

if __name__ == "__main__":
    main()
