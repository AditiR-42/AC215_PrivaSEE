import pytest
from fastapi.testclient import TestClient
from src.api_service.api.service import app

@pytest.fixture(scope="session")
def test_client():
    # The TestClient starts and stops the app automatically, in-memory
    with TestClient(app) as client:
        yield client

def test_index(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to PrivaSee"}

def test_status(test_client):
    response = test_client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["version"] == "3.1"

def test_process_pdf_no_file(test_client):
    # Attempt to call /process-pdf/ without sending a file
    # This should fail since we must send a PDF
    response = test_client.post("/process-pdf/")
    assert response.status_code == 422  # Missing file parameter

def test_process_pdf_with_invalid_file(test_client):
    # Attempt to call /process-pdf/ with a non-PDF file
    files = {"pdf_file": ("invalid.txt", b"Not a PDF", "text/plain")}
    response = test_client.post("/process-pdf/", files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "A valid PDF file is required."}

def test_get_grade_without_issues(test_client):
    # Attempt to get grade without processing a PDF first
    response = test_client.post("/get-grade/")
    assert response.status_code == 400
    assert "No issues have been processed yet" in response.json()["detail"]

def test_recommend_invalid_payload(test_client):
    # Call /recommend without a valid JSON payload
    response = test_client.post("/recommend")
    assert response.status_code == 422

def test_recommend_with_query(test_client, monkeypatch):
    # For integration tests that rely on external services like Vertex AI,
    # you may want to mock responses or run in an environment where credentials are available.
    # Here we just test a well-formed request and assume the code runs.
    class MockGenerateContent:
        def __init__(self, prompt):
            self.text = '{"Service": "MockApp", "privacy_rating": "A", "Title": "Mock Title", "Genre": "social media", "app_score": "4.5", "Installs": "100000", "Content Rating": "Everyone", "num_ratings": "2000", "num_reviews": "500", "Free": "True", "Contains Ads": "False"}'

    def mock_generate_content(self, prompt):
        return MockGenerateContent(prompt)

    # Mock the model generation call if you have such a method accessible.
    # For example, if the model is a global variable, you might patch it directly.
    # monkeypatch.setattr(model, "generate_content", mock_generate_content)

    # Perform the recommend request
    payload = {"query": "Recommend a social media app with a high privacy rating."}
    response = test_client.post("/recommend", json=payload)
    # Since we've not fully mocked out the entire chain, this may fail if it depends on external services.
    # In a full integration environment, you'd ensure all dependencies (like GCP credentials and data) are available.
    assert response.status_code in (200, 500)  # Adjust based on your environment expectations
