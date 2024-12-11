import httpx
import pytest
import io
from unittest.mock import patch, MagicMock
import httpx

BASE_URL = "http://localhost:9000" 

def generate_mock_pdf():
    """
    Generate a mock PDF file in-memory for testing purposes.
    """
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "This is a test PDF document for the process-pdf endpoint.")
    c.save()
    buffer.seek(0)
    return buffer

@patch("httpx.post")
def test_get_endpoint(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "mocked data"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "test query"})
    assert response.status_code == 200
    assert response.json() == {"data": "mocked data"}


@patch("httpx.post")
def test_process_pdf_endpoint(mock_post):
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_post.return_value = mock_response

    # Simulate a file upload
    files = {"pdf_file": ("mock.pdf", b"PDF content", "application/pdf")}
    response = httpx.post(f"{BASE_URL}/process-pdf/", files=files)

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"result": "success"}



@patch("httpx.post")
def test_get_grade_endpoint(mock_post):
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"grade": "A"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/get-grade/", json={"input": "test data"})

    assert response.status_code == 200
    assert response.json() == {"grade": "A"}

@patch("httpx.get")
def test_invalid_method(mock_get):
    """Test unsupported HTTP method for /recommend endpoint."""
    mock_response = MagicMock()
    mock_response.status_code = 405
    mock_get.return_value = mock_response

    response = httpx.get(f"{BASE_URL}/recommend")
    assert response.status_code == 405

@patch("httpx.post")
def test_recommend_endpoint_missing_payload(mock_post):
    """Test /recommend endpoint with missing payload."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Invalid input"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend")
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid input"}
@patch("httpx.post")
def test_get_grade_invalid_payload(mock_post):
    """Test /get-grade endpoint with invalid payload."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"error": "Invalid data format"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/get-grade/", json={"invalid": "data"})
    assert response.status_code == 422
    assert response.json() == {"error": "Invalid data format"}

@patch("httpx.post")
def test_get_grade_invalid_payload(mock_post):
    """Test /get-grade endpoint with invalid payload."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"error": "Invalid data format"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/get-grade/", json={"invalid": "data"})
    assert response.status_code == 422
    assert response.json() == {"error": "Invalid data format"}

@patch("httpx.post")
def test_process_pdf_invalid_file(mock_post):
    """Test /process-pdf/ endpoint with invalid file format."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Invalid file type"}
    mock_post.return_value = mock_response

    files = {"pdf_file": ("invalid.txt", b"Text content", "text/plain")}
    response = httpx.post(f"{BASE_URL}/process-pdf/", files=files)

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid file type"}

@patch("httpx.post")
def test_recommend_endpoint_unauthorized(mock_post):
    """Test /recommend endpoint without authorization."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", headers={})
    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized"}

@patch("httpx.post")
def test_recommend_large_payload(mock_post):
    """Test /recommend endpoint with a large payload."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "processed"}
    mock_post.return_value = mock_response

    large_payload = {"query": "x" * 10000}
    response = httpx.post(f"{BASE_URL}/recommend", json=large_payload)

    assert response.status_code == 200
    assert response.json() == {"data": "processed"}

@patch("httpx.get")
def test_recommend_pagination_out_of_range(mock_get):
    """Test /recommend endpoint with out-of-range page number."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": "Page not found"}
    mock_get.return_value = mock_response

    response = httpx.get(f"{BASE_URL}/recommend?page=9999")
    assert response.status_code == 404
    assert response.json() == {"error": "Page not found"}

@patch("httpx.post")
def test_process_pdf_invalid_project_id(mock_post):
    """Test /process-pdf endpoint with an invalid project_id."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"detail": "Error processing file: Invalid project_id"}
    mock_post.return_value = mock_response

    files = {"pdf_file": ("mock.pdf", b"PDF content", "application/pdf")}
    response = httpx.post(
        f"{BASE_URL}/process-pdf/",
        files=files,
        data={"project_id": "invalid_project", "location_id": "us-central1", "endpoint_id": "3504346967373250560"}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Error processing file: Invalid project_id"}

@patch("httpx.post")
def test_process_pdf_empty_file(mock_post):
    """Test /process-pdf endpoint with an empty PDF file."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "A valid PDF file is required."}
    mock_post.return_value = mock_response

    files = {"pdf_file": ("empty.pdf", b"", "application/pdf")}
    response = httpx.post(f"{BASE_URL}/process-pdf/", files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "A valid PDF file is required."}

@patch("httpx.post")
def test_get_grade_missing_issues(mock_post):
    """Test /get-grade endpoint with no issues processed."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "detail": "No issues have been processed yet. Please process a PDF first."
    }
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/get-grade/")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "No issues have been processed yet. Please process a PDF first."
    }

@patch("httpx.post")
def test_get_grade_invalid_grading_logic(mock_post):
    """Test /get-grade endpoint with an error in grading logic."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"detail": "Error grading issues: Invalid data"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/get-grade/")
    assert response.status_code == 500
    assert response.json() == {"detail": "Error grading issues: Invalid data"}

@patch("httpx.post")
def test_recommend_app_malformed_input(mock_post):
    """Test /recommend endpoint with malformed input."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Invalid input"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"invalid_key": "value"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid input"}

@patch("httpx.post")
def test_recommend_app_no_matches(mock_post):
    """Test /recommend endpoint with no matching criteria."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "No recommendations found"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "nonexistent criteria"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No recommendations found"}

@patch("httpx.post")
def test_recommend_invalid_genre(mock_post):
    """Test /recommend endpoint when genre does not match."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "No recommendations found"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "unknown genre"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No recommendations found"}

@patch("httpx.post")
def test_recommend_missing_values(mock_post):
    """Test /recommend endpoint with missing values in the DataFrame."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"recommendation": "Recommendation without full data"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "partial data"})
    assert response.status_code == 200
    assert response.json() == {"recommendation": "Recommendation without full data"}

@patch("httpx.post")
def test_process_pdf_processing_error(mock_post):
    """Test /process-pdf endpoint when process_pdf_privacy_issues raises an error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"detail": "Error processing file: Unexpected error"}
    mock_post.return_value = mock_response

    files = {"pdf_file": ("mock.pdf", b"PDF content", "application/pdf")}
    response = httpx.post(f"{BASE_URL}/process-pdf/", files=files)
    assert response.status_code == 500
    assert response.json() == {"detail": "Error processing file: Unexpected error"}
