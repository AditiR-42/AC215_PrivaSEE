import os
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
import logging
from api_service.api.utils.process_pdf import process_pdf_privacy_issues
from api_service.api.utils.privacy_grader import PrivacyGrader
import traceback

# Initialize the FastAPI router
router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# In-memory storage for extracted issues
parsed_issues_storage = {"issues": []}

@router.post("/process-pdf/")
async def process_pdf(
    pdf_file: UploadFile = File(...),
    project_id: str = "473358048261",
    location_id: str = "us-central1",
    endpoint_id: str = "3504346967373250560",
):
    """
    Process a PDF file to extract and analyze privacy issues.
    """
    try:
        # Validate uploaded file
        if not pdf_file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="A valid PDF file is required.")

        # Save the PDF to a temporary path
        pdf_path = "/tmp/uploaded_pdf.pdf"
        with open(pdf_path, "wb") as pdf_out:
            pdf_out.write(await pdf_file.read())

        # Process the PDF to extract privacy issues
        found_issues = process_pdf_privacy_issues(
            pdf_path, project_id, location_id, endpoint_id
        )

        # Store extracted issues in memory
        parsed_issues_storage["issues"] = found_issues

        return {
            "message": "Processing completed successfully.",
            "found_issues": found_issues,
        }

    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/get-grade/")
async def get_grade():
    """
    Grade the parsed privacy issues.
    """
    try:
        # Check if issues have been extracted
        if not parsed_issues_storage["issues"]:
            raise HTTPException(
                status_code=400,
                detail="No issues have been processed yet. Please process a PDF first.",
            )

        # Dynamically locate the CSV file in the "utils" directory one level above the current script's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)  # Get the parent directory
        mapping_df_path = os.path.join(parent_dir, "utils", "mapping_df.csv")
        category_weights_path = os.path.join(parent_dir, "utils", "category_weights.csv")

        # Initialize the PrivacyGrader
        grader = PrivacyGrader(mapping_df_path, category_weights_path)

        # Grade the issues
        report = grader.grade_privacy_issues(parsed_issues_storage["issues"])

        return {
            "overall_grade": report.overall_grade,
            "overall_score": report.overall_score,
            "category_scores": report.parent_category_grades,
        }

    except Exception as e:
        logging.error(f"Error grading issues: {str(e)}")
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error grading issues: {str(e)}")
