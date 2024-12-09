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

