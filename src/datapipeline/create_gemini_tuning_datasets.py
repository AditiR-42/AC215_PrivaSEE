import pandas as pd
import numpy as np
import json
from google.cloud import storage
from sklearn.model_selection import train_test_split
import io
import os
import random

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


def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Upload a file to GCS."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"Uploaded {source_file_name} to {destination_blob_name}")


# Group issues by service name and full text
def group_df_by_issues(df):
    """Group issues by service name and full text, aggregating issues into lists."""
    grouped_df = (
        df.groupby(["service", "full_text_clean"])["privacy_issue_clean"]
        .apply(list)  # Collect issues into a list
        .reset_index()
    )
    return grouped_df


def return_all_labels(df):
    """takes in df and returns all unique privacy issues"""
    return list(df.privacy_issue.unique())


def row_to_json(row):
    return {
        "systemInstruction": {
            "role": "system",
            "parts": [
                {"text": row["system_instruction"]}
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": row["question"]}
                ]
            },
            {
                "role": "model",
                "parts": [
                    {"text": row["answer"]}
                ]
            }
        ]
    }


def save_to_jsonl(data, file_name):
    """Save a list of dictionaries to a JSONL file."""
    with open(file_name, "w") as f:
        for entry in data:
            json.dump(entry, f)
            f.write("\n")


def read_jsonl(filename, num_lines=5):
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            if i >= num_lines:  # Stop after printing the specified number of lines
                break
            json_data = json.loads(line)
            print(json.dumps(json_data, indent=2))  # Pretty print each JSON object


def main():
    bucket_name = 'legal-terms-data'
    source_blob_name = 'tosdr-data/clean/cleaned_output2.csv'
    train_destination_blob_name = 'tosdr-data/modeling/train/train_gemini.jsonl'
    val_destination_blob_name = 'tosdr-data/modeling/val/val_gemini.jsonl'
    test_destination_blob_name = 'tosdr-data/modeling/test/test_gemini.jsonl'
    # Read the CSV from GCS
    df = read_csv_from_gcs(bucket_name, source_blob_name)

    print("finished reading in data")
    df.head()
    all_labels = return_all_labels(df)
    # System instructions
    labels_str = ', '.join(all_labels)
    labels_str
    print("finished getting all the labels")

    # Group issues by service name and full text
    grouped_df = group_df_by_issues(df)
    print("finished grouping the data by service and privacy issue")
    # Instructions for the system
    instruction = f"You should classify the text into one or more of the following classes: [{labels_str}]"
    grouped_df['system_instruction'] = instruction
    # User prompts
    # Define user prompts
    prompts = [
        "What privacy issues can be found in ",
        "Highlight privacy concerns in ",
        "Can you tell me about ",
        "Point out privacy risks in "
    ]
    # Calculate the size for each 25% split
    n = len(grouped_df)
    split_size = n // 4  # Integer division
    # Create an array where each prompt is repeated evenly across the dataset
    repeated_prompts = np.concatenate([
        [prompts[i]] * split_size for i in range(4)
    ])
    # repeated_prompts
    # In case the dataset size isn't perfectly divisible by 4, handle remaining rows
    remaining = n % 4
    if remaining > 0:
        repeated_prompts = np.concatenate([repeated_prompts, prompts[:remaining]])

    # Shuffle the prompts to avoid any pattern or bias
    np.random.shuffle(repeated_prompts)
    len(repeated_prompts)
    grouped_df["question"] = repeated_prompts + grouped_df["full_text_clean"]

    # Design model response
    # Convert lists to comma-separated strings
    grouped_df['answer'] = grouped_df['privacy_issue_clean'].apply(lambda x: ','.join(x) if isinstance(x, list) else x)
    json_data = grouped_df[["system_instruction", "question", "answer"]].apply(row_to_json, axis=1).tolist()
    print("Finished formatting data in system instruction, user, model for gemini")
    # Shuffle the data to ensure randomness
    random.shuffle(json_data)
    train_data, temp_data = train_test_split(json_data, test_size=0.2, random_state=42)
    val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

    print(len(train_data), len(val_data), len(test_data))
    print("finished train/val/test/split")
    save_to_jsonl(train_data, "train_gemini.jsonl")
    save_to_jsonl(val_data, "val_gemini.jsonl")
    save_to_jsonl(test_data, "test_gemini.jsonl")
    print("finished saving train/val/test split to jsonl")
    # Upload JSONL files to GCS
    upload_to_gcs(bucket_name=bucket_name, source_file_name="train_gemini.jsonl",
                  destination_blob_name=train_destination_blob_name)
    upload_to_gcs(bucket_name=bucket_name, source_file_name="val_gemini.jsonl",
                  destination_blob_name=val_destination_blob_name)
    upload_to_gcs(bucket_name=bucket_name, source_file_name="test_gemini.jsonl",
                  destination_blob_name=test_destination_blob_name)

if __name__ == "__main__":
    main()
