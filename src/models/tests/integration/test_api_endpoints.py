import httpx
import pytest
import io

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

def test_get_endpoint():
    response = httpx.post(f"{BASE_URL}/recommend", json={"query": "test query"})
    assert response.status_code == 200

def test_process_pdf_endpoint():
    """
    Test the /process-pdf/ endpoint with a mock PDF.
    """
    mock_pdf = generate_mock_pdf()
    files = {"pdf_file": ("mock.pdf", mock_pdf, "application/pdf")}
    response = httpx.post(f"{BASE_URL}/process-pdf/", files=files)
    assert response.status_code == 200
    assert "found_issues" in response.json()


def test_get_grade_endpoint():
    response = httpx.post(f"{BASE_URL}/get-grade/")
    if response.status_code == 400:
        assert response.json()["detail"] == "No issues have been processed yet. Please process a PDF first."
    else:
        assert response.status_code == 200
        data = response.json()
        assert "overall_grade" in data
        assert "overall_score" in data
        assert "category_scores" in data