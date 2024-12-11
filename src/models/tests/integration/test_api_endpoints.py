import httpx
import pytest
import io
from unittest.mock import patch, MagicMock
import pandas as pd

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

@patch("httpx.post")
def test_process_pdf_invalid_extension(mock_post):
    """Test /process-pdf endpoint with a non-PDF file."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "A valid PDF file is required."}
    mock_post.return_value = mock_response

    files = {"pdf_file": ("invalid.txt", b"Not a PDF", "text/plain")}
    response = httpx.post(f"{BASE_URL}/process-pdf/", files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "A valid PDF file is required."}

@patch("httpx.post")
def test_process_pdf_no_file(mock_post):
    """Test /process-pdf endpoint without a file."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"detail": "Missing file"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/process-pdf/", files={})
    assert response.status_code == 422
    assert response.json() == {"detail": "Missing file"}

@patch("httpx.post")
def test_get_grade_empty_storage(mock_post):
    """Test /get-grade endpoint with no issues processed."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "No issues have been processed yet."}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/get-grade/")
    assert response.status_code == 400
    assert response.json() == {"detail": "No issues have been processed yet."}

@patch("httpx.post")
def test_recommend_app_empty_query(mock_post):
    """Test /recommend endpoint with an empty query."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Query cannot be empty"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Query cannot be empty"}

@patch("httpx.post")
def test_recommend_app_invalid_json(mock_post):
    """Test /recommend endpoint with malformed JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"detail": "Invalid JSON payload"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", data="Invalid JSON")
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid JSON payload"}

@patch("httpx.post")
def test_recommend_app_partial_match(mock_post):
    """Test /recommend endpoint with partial matching criteria."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"recommendation": "Partial match app"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "social app with ads"})
    assert response.status_code == 200
    assert response.json() == {"recommendation": "Partial match app"}

@patch("httpx.post")
def test_recommend_app_large_dataset(mock_post):
    """Test /recommend endpoint with a large dataset."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"recommendation": "Best app from large dataset"}
    mock_post.return_value = mock_response

    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "app for students"})
    assert response.status_code == 200
    assert response.json() == {"recommendation": "Best app from large dataset"}

@patch("os.path.exists", return_value=False)
def test_process_pdf_missing_file(mock_exists):
    """Test /process-pdf when the file is missing."""
    pdf_path = "/tmp/nonexistent_pdf.pdf"
    with pytest.raises(FileNotFoundError, match="No such file or directory"):
        open(pdf_path, "rb")

@patch("os.path.exists", return_value=False)
def test_get_grade_missing_csv_files(mock_exists):
    """Test /get-grade when CSV files are missing."""
    with pytest.raises(FileNotFoundError):
        open("invalid_mapping_df.csv", "r")

def test_get_grade_empty_issues():
    """Test /get-grade with no issues in parsed_issues_storage."""
    parsed_issues_storage = {"issues": []}  # Simulate empty storage
    assert len(parsed_issues_storage["issues"]) == 0

@patch("api_service.api.routers.recommend.load_dataset")
def test_load_dataset(mock_load_dataset):
    """Test lazy loading of dataset with mocked data."""
    # Mock the load_dataset function to return a fake DataFrame
    mock_load_dataset.return_value = pd.DataFrame(
        {"formatted": ["mock_data"], "privacy_rating": ["A"], "Genre": ["Social Media"]}
    )

    # Import initialize_dataset and relevant globals from recommend.py
    from api_service.api.routers.recommend import initialize_dataset, df, formatted_data

    # Ensure the dataset is not initialized yet
    assert df is None

    # Call initialize_dataset, which should now use the mocked load_dataset
    initialize_dataset()

    # Verify that df and formatted_data are properly initialized
    assert df is not None
    assert not df.empty
    assert df.iloc[0]["formatted"] == "mock_data"
    assert formatted_data == ["mock_data"]

@patch("api_service.api.routers.recommend.storage.Client")
def test_load_dataset_mock_storage(mock_storage_client):
    """Test load_dataset function with mocked Google Cloud Storage."""
    # Mock the blob's download_as_text method to return CSV data
    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = "formatted,privacy_rating,Genre\nmock_data,A,Social Media"

    # Mock the bucket and its blob method
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    # Mock the storage.Client to return the mocked bucket
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    # Import and test the load_dataset function
    from api_service.api.routers.recommend import load_dataset

    # Call the function and assert the output
    df = load_dataset()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["formatted"] == "mock_data"
    assert df.iloc[0]["privacy_rating"] == "A"
    assert df.iloc[0]["Genre"] == "Social Media"

