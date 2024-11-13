import fitz  # PyMuPDF for PDF extraction
import vertexai
import os
from vertexai.generative_models import GenerativeModel
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text

# Initialize Vertex AI with the Generative Model
def initialize_vertex_ai(project_id: str, region: str):
    vertexai.init(project=project_id, location=region)

# Function to call the Gemini model using GenerativeModel
def call_gemini_model(input_text: str) -> List[str]:
    """
    Sends a request to the Gemini model on Vertex AI and returns identified privacy issues.
    """
    # Load the generative model
    model = GenerativeModel("gemini-1.5-flash-002")
    
    # Generate content by prompting the model to analyze privacy issues
    response = model.generate_content(
        f"Identify privacy issues in the following text:\n\n{input_text}"
    )
    
    # Split response text into issues if they are listed line by line
    found_issues = response.text.strip().splitlines()
    return found_issues

# Placeholder function to validate found issues
def validate_found_issues(found_issues: List[str]) -> List[str]:
    """Validates found issues. (Assume all issues from Gemini are valid for now)."""
    # If validation logic is added later, it would go here.
    return found_issues

# Function to process PDF and print issues
def process_pdf_privacy_issues(pdf_path: str, project_id: str, region: str):
    # Step 1: Extract text from PDF
    input_text = extract_text_from_pdf(pdf_path)

    # Step 2: Get privacy issues from the Gemini model
    found_issues = call_gemini_model(input_text)

    # Step 3: Validate issues
    validated_issues = validate_found_issues(found_issues)

    # Step 4: Print validated issues for grading or further processing
    print("Validated Found Issues to be graded:")
    for issue in validated_issues:
        print(f"- {issue}")

# Example usage
if __name__ == "__main__":
    project_id = "ac215-privasee"
    region = "us-central1"
    initialize_vertex_ai(project_id, region)

    # Path to the PDF file
    pdf_path = os.getenv("PDF_PATH", "/pdf_directory/default.pdf")
    process_pdf_privacy_issues(pdf_path, project_id, region)