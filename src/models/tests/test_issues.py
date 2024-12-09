import pytest
import fitz
from unittest.mock import patch, MagicMock
from models.get_issues import extract_text_from_pdf, process_pdf_privacy_issues
import pandas as pd

# Fixture to create a temporary PDF with known content for testing
@pytest.fixture
def mock_pdf_with_content(tmp_path):
    pdf_path = tmp_path / "mock_test.pdf"
    doc = fitz.open()  
    page = doc.new_page()
    test_content = "This is a test PDF containing text."
    page.insert_text((72, 72), test_content)
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path), test_content

@pytest.fixture
def mock_csv_file(tmp_path):
    csv_path = tmp_path / "mock_mapping.csv"
    data = {
        "parent_issue": ["ownership", "permissions"],
        "privacy_issue": ["this service takes credit for your content", "the app requires broad device permissions"]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)


# Unit Test: Test PDF text extraction
def test_extract_text_from_pdf(mock_pdf_with_content):
    pdf_path, expected_text = mock_pdf_with_content
    extracted_text = extract_text_from_pdf(pdf_path)
    assert extracted_text.strip() == expected_text, "Extracted text should match the content of the PDF."


# Unit Test: Test Vertex AI initialization and chat response with mocks
def test_process_pdf_privacy_issues(mock_pdf_with_content, mock_csv_file):
    pdf_path, test_content = mock_pdf_with_content
    project_id = "mock_project_id"
    location_id = "mock_location"
    endpoint_id = "mock_endpoint"
    csv_path = mock_csv_file

    mock_response = MagicMock()
    mock_response.text = "Mocked response about privacy issues."

    with patch("models.get_issues.vertexai.init") as mock_init, \
         patch("models.get_issues.GenerativeModel") as MockGenerativeModel, \
         patch("builtins.print") as mock_print:

        # Mock the Vertex AI initialization
        mock_init.return_value = None

        # Mock the generative model and chat session
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.start_chat.return_value.send_message.return_value = mock_response

        # Call the function
        process_pdf_privacy_issues(pdf_path, csv_path, project_id, location_id, endpoint_id)

        # Verify Vertex AI initialization
        mock_init.assert_called_once_with(project=project_id, location=location_id)

        # Verify the model and chat methods were called
        MockGenerativeModel.assert_called_once_with(
            f"projects/{project_id}/locations/{location_id}/endpoints/{endpoint_id}"
        )
        mock_model_instance.start_chat.return_value.send_message.assert_called_once()

        # Verify the printed output
        # Verify the printed output
        mock_print.assert_any_call("Identified privacy attributes:")
        mock_print.assert_any_call(f"- Unknown: {mock_response.text}")



# End-to-End Test: Simulate an integration flow
def test_end_to_end_process(mock_pdf_with_content, mock_csv_file):
    pdf_path, test_content = mock_pdf_with_content
    project_id = "mock_project_id"
    location_id = "mock_location"
    endpoint_id = "mock_endpoint"
    csv_path = mock_csv_file

    mock_response = MagicMock()
    mock_response.text = "Identified privacy issue: Example Issue"

    with patch("models.get_issues.vertexai.init") as mock_init, \
         patch("models.get_issues.GenerativeModel") as MockGenerativeModel, \
         patch("builtins.print") as mock_print:

        # Mock Vertex AI initialization
        mock_init.return_value = None

        # Mock generative model and chat session
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.start_chat.return_value.send_message.return_value = mock_response

        # Run the process function
        process_pdf_privacy_issues(pdf_path, csv_path, project_id, location_id, endpoint_id)

        # Verify all critical components executed correctly
        mock_init.assert_called_once_with(project=project_id, location=location_id)
        MockGenerativeModel.assert_called_once()
        mock_model_instance.start_chat.return_value.send_message.assert_called_once()

        # Validate final response was printed
        mock_print.assert_any_call("Identified privacy attributes:")      
        # mock_print.assert_any_call(mock_response.text)
        mock_print.assert_any_call(f"- Unknown: {mock_response.text}")