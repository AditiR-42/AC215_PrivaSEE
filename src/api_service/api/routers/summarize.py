from fastapi import APIRouter, UploadFile, HTTPException, Form, File
import logging
from api.utils.process_pdf import process_pdf_privacy_issues
from api.utils.privacy_grader import PrivacyGrader

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
    endpoint_id: str = "5609779793168957440",
):
    """
    Process a PDF file to extract and analyze privacy issues.
    """
    try:
        logging.info("Received PDF for processing.")

        # Validate uploaded file
        if not pdf_file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="A valid PDF file is required.")

        # Save the PDF to a temporary path
        pdf_path = "/tmp/uploaded_pdf.pdf"
        with open(pdf_path, "wb") as pdf_out:
            pdf_out.write(await pdf_file.read())

        logging.info("PDF saved to temporary storage. Starting processing.")

        # Process the PDF to extract privacy issues
        found_issues = process_pdf_privacy_issues(
            pdf_path, project_id, location_id, endpoint_id
        )

        # Store extracted issues in memory
        parsed_issues_storage["issues"] = found_issues

        logging.info(f"Processing completed. Found issues: {found_issues}")

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
        logging.info("Grading issues...")

        # Check if issues have been extracted
        if not parsed_issues_storage["issues"]:
            raise HTTPException(
                status_code=400,
                detail="No issues have been processed yet. Please process a PDF first.",
            )

        # Initialize the PrivacyGrader
        grader = PrivacyGrader("/Users/sammizhu/ac215_PrivaSEE/src/api_service/api/utils/mapping_df.csv")

        # Grade the issues
        report = grader.grade_privacy_issues(parsed_issues_storage["issues"])

        logging.info(f"Grading completed. Report: {report}")

        return {
            "overall_grade": report["overall_grade"],
            "overall_score": report["overall_score"],
            "category_scores": report["category_scores"],
        }

    except Exception as e:
        logging.error(f"Error grading issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error grading issues: {str(e)}")