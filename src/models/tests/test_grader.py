import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from io import StringIO
from models.privacy_grader import PrivacyGrader, load_weights_from_csv

@patch("models.privacy_grader.get_storage_client")
def test_privacy_grader(mock_get_storage_client):
    print("Mocking get_storage_client...")
    mock_storage_client = MagicMock()
    mock_get_storage_client.return_value = mock_storage_client

    mock_bucket = mock_storage_client.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.download_as_text.return_value = "privacy_issue,parent_issue,classification\nissue1,category1,neutral"

    mapping_df = pd.DataFrame({
        "privacy_issue": ["test_issue"],
        "parent_issue": ["test_category"],
        "classification": ["neutral"]
    })
    category_weights = {"test_category": 1.0}
    grader = PrivacyGrader(mapping_df, category_weights)

    assert grader is not None



# to  test do PYTHONPATH=$(pwd) pytest tests/test_grader.py
# Mock CSV content for testing based on provided files
WEIGHTS_CSV = """parent_category,weight
Ownership,0.4
Data Protection,0.3
Device Permissions,0.2
User Rights,0.1
"""

MAPPING_CSV = """parent_issue,privacy_issue
Ownership,This service takes credit for your content
Ownership,If you offer suggestions to the service they become the owner
Ownership,You maintain ownership of your content
Ownership,This service can use your content for all their purposes
Data Protection,This service shares your data with third parties
Device Permissions,The app requires broad device permissions
User Rights,You can delete your content from the service
"""

@pytest.fixture
def mock_weights():
    """Fixture for loading mock weights CSV."""
    return pd.read_csv(StringIO(WEIGHTS_CSV))

@pytest.fixture
def mock_mapping_df():
    """Fixture for loading mock mapping CSV."""
    return pd.read_csv(StringIO(MAPPING_CSV))

@pytest.fixture
def mock_category_weights():
    """Fixture for loading mock category weights dictionary."""
    return {
        "Ownership": 0.4,
        "Data Protection": 0.3,
        "Device Permissions": 0.2,
        "User Rights": 0.1,
    }

@pytest.fixture
def grader(mock_mapping_df, mock_category_weights):
    """Fixture for initializing the PrivacyGrader."""
    return PrivacyGrader(mapping_df=mock_mapping_df, category_weights=mock_category_weights)

# Unit test: Tests loading weights from CSV to dictionary format
def test_load_weights_from_csv():
    """Test loading weights from CSV."""
    filepath = StringIO(WEIGHTS_CSV)
    expected = {
        "Ownership": 0.4,
        "Data Protection": 0.3,
        "Device Permissions": 0.2,
        "User Rights": 0.1,
    }
    result = load_weights_from_csv(filepath)
    assert result == expected

# Integration test: Ensures the mapping between cases and issues is created accurately
def test_create_case_mapping(grader, mock_mapping_df):
    """Test creation of case mapping."""
    expected_mapping = {
        "this service takes credit for your content": "This service takes credit for your content",
        "if you offer suggestions to the service they become the owner": "If you offer suggestions to the service they become the owner",
        "you maintain ownership of your content": "You maintain ownership of your content",
        "this service can use your content for all their purposes": "This service can use your content for all their purposes",
        "this service shares your data with third parties": "This service shares your data with third parties",
        "the app requires broad device permissions": "The app requires broad device permissions",
        "you can delete your content from the service": "You can delete your content from the service",
    }
    result = grader._create_case_mapping(mock_mapping_df)
    assert result == expected_mapping

# Integration test: Tests if the category mapping is created correctly from mock data
def test_create_category_mapping(grader):
    """Test creation of category mapping."""
    expected_mapping = {
        "Ownership": [
            "this service takes credit for your content",
            "if you offer suggestions to the service they become the owner",
            "you maintain ownership of your content",
            "this service can use your content for all their purposes",
        ],
        "Data Protection": ["this service shares your data with third parties"],
        "Device Permissions": ["the app requires broad device permissions"],
        "User Rights": ["you can delete your content from the service"],
    }
    result = grader._create_category_mapping()
    assert result == expected_mapping

# Integration test: Ensures issues are validated against the known mapping
def test_validate_issues(grader):
    """Test validation of privacy issues."""
    found_issues = [
        "This service takes credit for your content",
        "The app requires broad device permissions"
    ]
    valid_issues, unknown_issues = grader._validate_issues(found_issues)
    assert valid_issues == [
        "this service takes credit for your content",
        "the app requires broad device permissions"
    ]

# Integration test: Checks that category scores are calculated based on issues found
def test_calculate_category_scores(grader):
    """Test calculation of category scores."""
    valid_issues = [
        "Ownership: this service takes credit for your content",
        "Device Permissions: the app requires broad device permissions"
    ]
    result = grader._calculate_category_scores(valid_issues)
    expected_scores = {
        "Ownership": 0.75,  # 3 out of 4 issues not found
        "Data Protection": 1.0,  # No issues found
        "Device Permissions": 0.0,  # All issues found
        "User Rights": 1.0,  # No issues found
    }
    assert result == expected_scores

# Integration test: Verifies overall score calculation from category scores and weights
def test_calculate_overall_score(grader):
    """Test calculation of overall score."""
    category_scores = {
        "Ownership": 0.75,
        "Data Protection": 1.0,
        "Device Permissions": 0.0,
        "User Rights": 1.0,
    }
    result = grader._calculate_overall_score(category_scores)
    expected_score = (0.75 * 0.4 + 1.0 * 0.3 + 0.0 * 0.2 + 1.0 * 0.1) / (0.4 + 0.3 + 0.2 + 0.1)
    assert result == expected_score

# Unit test: Checks if scores are correctly converted to letter grades
def test_get_grade(grader):
    """Test grade conversion based on score."""
    assert grader._get_grade(0.85) == Grade.A
    assert grader._get_grade(0.65) == Grade.B
    assert grader._get_grade(0.45) == Grade.C
    assert grader._get_grade(0.25) == Grade.D
    assert grader._get_grade(0.15) == Grade.F

# System test: Verifies the grading of privacy issues and generating a report
def test_grade_privacy_issues(grader):
    """Test grading privacy issues and generating a report."""
    found_issues = [
        "Ownership: This service takes credit for your content",
        "Device Permissions: The app requires broad device permissions",
    ]
    report = grader.grade_privacy_issues(found_issues)

    assert isinstance(report, PrivacyReport)
    assert report.overall_grade == Grade.B.value
    assert report.parent_category_grades["Ownership"]["grade"] == "B"
    assert report.parent_category_grades["Device Permissions"]["grade"] == "F"
    assert report.parent_category_grades["Data Protection"]["grade"] == "A"
    assert report.parent_category_grades["User Rights"]["grade"] == "A"


