import pytest
import os
import fitz
from unittest.mock import patch, MagicMock
from get_issues import (
    extract_text_from_pdf,
    initialize_vertex_ai,
    call_gemini_model,
    validate_found_issues,
    process_pdf_privacy_issues
)
from google.api_core.exceptions import NotFound

# Fixture to create a sample PDF with known text for testing
@pytest.fixture
def mock_pdf_path_with_text(tmp_path):
    # Fixture to create a temporary PDF for testing extraction
    pdf_path = tmp_path / "test_text.pdf"
    doc = fitz.open()  # create a new PDF
    page = doc.new_page()
    text_content = "This is a test PDF with known text content."
    page.insert_text((72, 72), text_content)
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path), text_content

# Unit test: Testing PDF text extraction functionality
def test_extract_text_from_pdf(mock_pdf_path_with_text):
    pdf_path, expected_text = mock_pdf_path_with_text
    extracted_text = extract_text_from_pdf(pdf_path)
    assert extracted_text.strip() == expected_text, "The extracted content should match the known PDF text."

# Unit test: Mock Vertex AI initialization
def test_initialize_vertex_ai():
    with patch("vertexai.init") as mock_init:
        initialize_vertex_ai("project_id", "us-central1")
        mock_init.assert_called_once_with(project="project_id", location="us-central1")

# Unit test: Testing API call to the Gemini model for successful connection
def test_call_gemini_model_successful_connection():
    input_text = "Sample text with privacy issues."
    mock_response = MagicMock()
    mock_response.text = "Issue 1\nIssue 2\nIssue 3"
    
    with patch("get_issues.GenerativeModel") as MockGenerativeModel:
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.return_value = mock_response

        issues = call_gemini_model(input_text)
        
        # Verify successful connection response
        assert issues == ["Issue 1", "Issue 2", "Issue 3"], "Should match the simulated response."
        MockGenerativeModel.assert_called_once_with("gemini-1.5-flash-002")

# Unit test: Testing API call to the Gemini model for a 404 error
def test_call_gemini_model_404_error():
    input_text = "Sample text with privacy issues."
    
    with patch("get_issues.GenerativeModel") as MockGenerativeModel:
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = NotFound("404 error: Model not found.")
        
        with pytest.raises(NotFound, match="404 error: Model not found."):
            call_gemini_model(input_text)

# Unit test: Validate that found issues are processed correctly
def test_validate_found_issues():
    issues = ["Issue 1", "Issue 2"]
    validated_issues = validate_found_issues(issues)
    assert validated_issues == issues, "Validated issues should match the input issues."

# System test: End-to-end test of process_pdf_privacy_issues function
def test_process_pdf_privacy_issues(mock_pdf_path_with_text):
    pdf_path, _ = mock_pdf_path_with_text
    with patch("get_issues.call_gemini_model") as mock_call_gemini_model:
        mock_call_gemini_model.return_value = ["Issue 1", "Issue 2"]
        
        with patch("builtins.print") as mock_print:
            process_pdf_privacy_issues(pdf_path, "project_id", "us-central1")
            mock_print.assert_any_call("Validated Found Issues to be graded:")
            mock_print.assert_any_call("- Issue 1")
            mock_print.assert_any_call("- Issue 2")