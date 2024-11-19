import os
import fitz  # PyMuPDF for PDF extraction
import vertexai
import pandas as pd
from vertexai.generative_models import GenerativeModel

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text


def load_privacy_issues(csv_path: str) -> str:
    """Load privacy issues from CSV and format them as a string."""
    df = pd.read_csv(csv_path)
    # Combine parent issue and privacy issue into a single string for each row
    issues = "\n".join(
        f"{row['parent_issue']}: {row['privacy_issue']}" for _, row in df.iterrows()
    )
    return issues

# Define your generation configuration
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}


def process_pdf_privacy_issues(pdf_path: str, project_id: str, location_id: str, endpoint_id: str):
    """
    Extracts text from a PDF and sends it to the Vertex AI model for analysis.
    """
    # Step 1: Extract text from PDF
    input_text = extract_text_from_pdf(pdf_path)
    
    # Dynamically locate the CSV path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "mapping_df.csv")
    
    privacy_issues = load_privacy_issues(csv_path)
    
    # Step 2: Initialize Vertex AI
    vertexai.init(project=project_id, location=location_id)
    
    # Step 3: Initialize the Generative Model with your endpoint
    model = GenerativeModel(
        f"projects/{project_id}/locations/{location_id}/endpoints/{endpoint_id}"
    )
    
    # Step 4: Start a chat session
    chat = model.start_chat()
    
    # Step 5: Send messages to the model
    response = chat.send_message(
        [
            f"Privacy Issues List:\n{privacy_issues}",
            f"Extracted PDF Text:\n{input_text}",
            "Which privacy issues from the list are found in the text above?",
        ],
        generation_config=generation_config,
    )
    # Step 6: Print the response
    response_list = [item.strip() for item in response.text.split(',')]
    
    # Print the response for verification
    mapping_df = pd.read_csv(csv_path)
    mapping_dict = dict(zip(mapping_df['privacy_issue'].str.lower(), mapping_df['parent_issue']))

    # Format response list with parent issues
    formatted_response_list = []
    for issue in response_list:
        issue_lower = issue.lower()
        parent_issue = mapping_dict.get(issue_lower, "Unknown")
        formatted_response_list.append(f"{parent_issue}: {issue}")
    
    # Print the response for verification
    print("Model Response (with parent issues):")
    for issue in formatted_response_list:
        print(f"- {issue}")
    
    return formatted_response_list

# Example usage
if __name__ == "__main__":
    project_id = "473358048261"  # Your project ID
    location_id = "us-central1"  # Your region
    endpoint_id = "3317729057814085632"  # Your endpoint ID
    
    # Path to the PDF file
    pdf_path = os.getenv("PDF_PATH", "/pdf_directory/default.pdf")
    
    process_pdf_privacy_issues(pdf_path, project_id, location_id, endpoint_id)
