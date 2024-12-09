import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from io import StringIO
from models.privacy_grader import PrivacyGrader, load_weights_from_csv, Grade, PrivacyReport, get_storage_client

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

MAPPING_CSV = """parent_issue,privacy_issue,classification
Ownership,This service takes credit for your content,bad
Ownership,If you offer suggestions to the service they become the owner,neutral
Device Permissions,The app requires broad device permissions,bad
User Rights,You can delete your content from the service,good
Data Protection,This service shares your data with third parties,bad
"""


@pytest.fixture
def mock_weights():
    """Fixture for loading mock weights CSV."""
    return pd.read_csv(StringIO(WEIGHTS_CSV))

@pytest.fixture
def mock_mapping_df():
    data = """parent_issue,privacy_issue,classification
    Ownership,This service takes credit for your content,bad
    Ownership,If you offer suggestions to the service they become the owner,neutral
    Device Permissions,The app requires broad device permissions,bad
    User Rights,You can delete your content from the service,good
    Data Protection,This service shares your data with third parties,bad
    """
    df = pd.read_csv(StringIO(data))
    df['parent_issue'] = df['parent_issue'].str.strip()
    return df

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
    expected_mapping = {'this service takes credit for your content': 'This service takes credit for your content', 'if you offer suggestions to the service they become the owner': 'If you offer suggestions to the service they become the owner', 'the app requires broad device permissions': 'The app requires broad device permissions', 'you can delete your content from the service': 'You can delete your content from the service', 'this service shares your data with third parties': 'This service shares your data with third parties'}
    result = grader._create_case_mapping(mock_mapping_df)
    print("this is result", result)
    assert result == expected_mapping


# Integration test: Tests if the category mapping is created correctly from mock data
def test_create_category_mapping(grader):
    """Test creation of category mapping."""
    expected_mapping = {
        "Ownership": [
            "this service takes credit for your content",
            "if you offer suggestions to the service they become the owner",
        ],
        "Device Permissions": ["the app requires broad device permissions"],
        "User Rights": ["you can delete your content from the service"],
        "Data Protection": ["this service shares your data with third parties"],
    }
    result = grader._create_category_mapping()
    assert result == expected_mapping


# Integration test: Ensures issues are validated against the known mapping
def test_validate_issues(grader):
    """Test validation of privacy issues."""
    found_issues = [
        "Ownership: this service takes credit for your content",
        "Device Permissions: the app requires broad device permissions"
    ]
    valid_issues, unknown_issues = grader._validate_issues(found_issues)
    assert valid_issues == found_issues
    assert unknown_issues == []

# Integration test: Checks that category scores are calculated based on issues found
def test_calculate_category_scores(grader):
    """Test calculation of category scores."""
    valid_issues = [
        "Ownership: this service takes credit for your content",
        "Device Permissions: the app requires broad device permissions",
    ]
    result = grader._calculate_category_scores(valid_issues)
    expected_scores = {
        "Ownership":0.12000000000000002,  
        "Device Permissions": 0.06000000000000001,  # Severe penalty for bad issues
        "Data Protection": 1.0,  # No issues found
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
    assert grader._get_grade(0.95) == Grade.A
    assert grader._get_grade(0.85) == Grade.B
    assert grader._get_grade(0.75) == Grade.C
    assert grader._get_grade(0.65) == Grade.D
    assert grader._get_grade(0.55) == Grade.F

# System test: Verifies the grading of privacy issues and generating a report
def test_grade_privacy_issues(grader):
    """Test grading privacy issues and generating a report."""
    found_issues = [
        "Ownership: this service takes credit for your content",
        "Device Permissions: the app requires broad device permissions"
    ]
    report = grader.grade_privacy_issues(found_issues)

    assert report.overall_grade == "F"
    assert report.parent_category_grades["Ownership"].grade == "F"
    assert report.parent_category_grades["Device Permissions"].grade == "F"
    assert report.parent_category_grades["Data Protection"].grade == "A"
    assert report.parent_category_grades["User Rights"].grade == "A"

def test_worst_categories_edge_case(grader):
    """Test identifying worst categories when multiple have identical scores."""
    issues = [
        "Ownership: this service takes credit for your content",
        "Device Permissions: the app requires broad device permissions",
    ]
    report = grader.grade_privacy_issues(issues)
    worst_categories = report.worst_parent_categories
    assert len(worst_categories) == 2
    assert all(category.grade == "F" for category in worst_categories)

def test_load_weights_missing_column():
    """Test load_weights_from_csv with missing columns."""
    invalid_csv = StringIO("random_column\nvalue1")
    with pytest.raises(KeyError):
        load_weights_from_csv(invalid_csv)

def test_privacy_grader_empty_mapping_df():
    """Test PrivacyGrader with an empty mapping DataFrame."""
    mapping_df = pd.DataFrame(columns=["privacy_issue", "parent_issue", "classification"])
    grader = PrivacyGrader(mapping_df)
    assert grader.all_parent_categories == set()
    assert grader.valid_privacy_issues == set()

def test_create_category_mapping_empty(grader):
    """Test _create_category_mapping with no categories."""
    grader.mapping_df = pd.DataFrame(columns=["privacy_issue", "parent_issue", "classification"])
    grader.all_parent_categories = set()  # Reset categories
    result = grader._create_category_mapping()
    assert result == {}

def test_validate_issues_unusual_format(grader):
    """Test _validate_issues with unusual formatting."""
    issues = ["random text without separator", "Another random issue"]
    valid, unknown = grader._validate_issues(issues)
    assert valid == []
    assert unknown == issues

def test_restore_original_case_partial_match(grader):
    """Test _restore_original_case with partially matching issues."""
    issues = ["nonexistent issue", "this service takes credit for your content"]
    restored = grader._restore_original_case(issues)
    assert restored == ["nonexistent issue", "This service takes credit for your content"]

def test_validate_issues_valid_and_invalid(grader):
    """Test _validate_issues with a mix of valid and invalid issues."""
    issues = [
        "Ownership: this service takes credit for your content",
        "InvalidCategory: some unknown issue",
        "this is not formatted correctly",
    ]
    valid, unknown = grader._validate_issues(issues)
    assert valid == ["Ownership: this service takes credit for your content"]
    assert unknown == [
        "InvalidCategory: some unknown issue",
        "this is not formatted correctly",
    ]
def test_calculate_overall_score_equal_weights(grader):
    """Test _calculate_overall_score with equal weights."""
    grader.category_weights = {category: 1 for category in grader.all_parent_categories}
    category_scores = {category: 0.8 for category in grader.all_parent_categories}
    result = grader._calculate_overall_score(category_scores)
    assert result == 0.8  # Equal weights should average to the score value
def test_restore_original_case_partial(grader):
    """Test _restore_original_case with partially unmapped issues."""
    issues = ["this service takes credit for your content", "unknown issue"]
    restored = grader._restore_original_case(issues)
    assert restored == ["This service takes credit for your content", "unknown issue"]

def test_grade_privacy_issues_only_unknown(grader):
    """Test grade_privacy_issues when only unknown issues are present."""
    unknown_issues = ["InvalidCategory: this issue is invalid"]
    report = grader.grade_privacy_issues(unknown_issues)
    assert report is not None
    assert report.unknown_issues == unknown_issues
    assert report.overall_score == 100.0  # No valid issues = perfect score
def test_grade_privacy_issues_empty(grader):
    """Test grade_privacy_issues with no issues provided."""
    report = grader.grade_privacy_issues([])
    assert report is None

def test_load_weights_from_csv_malformed_data():
    """Test load_weights_from_csv with malformed data."""
    malformed_csv = StringIO("random\nvalue1")
    with pytest.raises(KeyError):
        load_weights_from_csv(malformed_csv)

def test_load_weights_from_csv_no_data():
    """Test load_weights_from_csv with no data in the file."""
    empty_csv = StringIO("")
    with pytest.raises(pd.errors.EmptyDataError):
        load_weights_from_csv(empty_csv)


def test_calculate_category_scores_no_issues(grader):
    """Test _calculate_category_scores when no issues are valid."""
    valid_issues = []
    scores = grader._calculate_category_scores(valid_issues)
    assert all(score == 1.0 for score in scores.values())

def test_save_grade_to_csv_missing_columns(tmp_path, capsys):
    """Test save_grade_to_csv when the CSV is missing required columns."""
    csv_path = tmp_path / "grades.csv"
    with open(csv_path, "w") as f:
        f.write("random_column\nvalue1")
    
    PrivacyGrader.save_grade_to_csv("TestService", "A", csv_path)

    captured = capsys.readouterr()
    assert "Error saving grade to CSV: 'service_name'" in captured.out

def test_save_grade_to_csv_multiple_services(tmp_path):
    """Test save_grade_to_csv with multiple services."""
    csv_path = tmp_path / "grades.csv"
    PrivacyGrader.save_grade_to_csv("Service1", "A", csv_path)
    PrivacyGrader.save_grade_to_csv("Service2", "B", csv_path)
    df = pd.read_csv(csv_path)
    assert df[df["service_name"] == "Service1"]["grade"].iloc[0] == "A"
    assert df[df["service_name"] == "Service2"]["grade"].iloc[0] == "B"