import fitz  # PyMuPDF for PDF extraction
import vertexai
from vertexai.generative_models import GenerativeModel

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text()
    return text

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
        [input_text, "Identify privacy issues in the following text:"],
        generation_config=generation_config,
    )    

    # # Step 6: Print the response
    print("Model Response:")
    print(response.text)
    

# Example usage
if __name__ == "__main__":
    project_id = "473358048261"  # Your project ID
    location_id = "us-central1"  # Your region
    endpoint_id = ""  # Your endpoint ID
    
    # Path to your PDF file
    pdf_path = "/Users/sammizhu/ac215_PrivaSEE/apple.pdf"
    
    process_pdf_privacy_issues(pdf_path, project_id, location_id, endpoint_id)