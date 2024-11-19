import os
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from models.get_issues import process_pdf_privacy_issues

def load_weights_from_csv(filepath: str) -> Dict[str, float]:
    """Load category weights from CSV file into format needed by grader."""
    df = pd.read_csv(filepath)
    return dict(zip(df['parent_category'], df['weight']))

def upload_df_to_gcs(bucket_name, df, destination_blob_name):
    """Uploads a DataFrame as a CSV to GCS directly from memory."""
    # Convert DataFrame to CSV string
    csv_data = df.to_csv(index=False)

    # Get the bucket and blob objects
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload the CSV string to GCS
    blob.upload_from_string(csv_data, content_type='text/csv')

    print(f"Uploaded DataFrame to {destination_blob_name} in bucket {bucket_name}.")

def read_csv_from_gcs(bucket_name, source_blob_name):
    """Read a CSV file from GCS into a DataFrame."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    # Download the CSV content as text (UTF-8)
    content = blob.download_as_text()
    # Read it directly into a DataFrame
    return pd.read_csv(io.StringIO(content))


class Grade(Enum):
    """Grade scale for privacy evaluations."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class PrivacyReport:
    """Container for privacy grading results."""
    overall_grade: str
    overall_score: float
    parent_category_grades: Dict[str, Dict]
    worst_parent_categories: List[Dict]
    unknown_issues: Optional[List[str]] = None


class PrivacyGrader:
    def __init__(self, mapping_df: pd.DataFrame, category_weights: Dict[str, float] = None):
        # Store mapping DataFrame and create set of valid issues (converted to lowercase)
        self.mapping_df = mapping_df.copy()
        self.mapping_df['privacy_issue'] = self.mapping_df['privacy_issue'].str.lower()
        self.valid_privacy_issues = set(self.mapping_df['privacy_issue'].unique())

        # Get all unique parent categories
        self.all_parent_categories = set(self.mapping_df['parent_issue'].unique())

        # Create mapping of parent categories to their child issues
        self.issues_by_category = self._create_category_mapping()

        # Create case mapping dictionary for preserving original case in reports
        self.case_mapping = self._create_case_mapping(mapping_df)

        # Set up category weights (default to equal weights if none provided)
        if category_weights is None:
            self.category_weights = {cat: 1.0 for cat in self.all_parent_categories}
        else:
            self.category_weights = category_weights

        # Define grade boundaries
        self.grade_boundaries = {
            0.8: Grade.A,
            0.6: Grade.B,
            0.4: Grade.C,
            0.2: Grade.D
        }

    def _create_case_mapping(self, original_df: pd.DataFrame) -> Dict[str, str]:
        """Create mapping of lowercase issues to their original case."""
        return dict(zip(original_df['privacy_issue'].str.lower(), original_df['privacy_issue']))

    def _create_category_mapping(self) -> Dict[str, List[str]]:
        """Create dictionary of all possible child issues by parent category."""
        category_mapping = {}
        for category in self.all_parent_categories:
            category_mapping[category] = self.mapping_df[
                self.mapping_df['parent_issue'] == category
                ]['privacy_issue'].tolist()
        return category_mapping

    def _validate_issues(self, found_issues: List[str]) -> Tuple[List[str], List[str]]:
        """Separate valid and unknown issues."""
        valid_issues = []
        unknown_issues = []

        for issue in found_issues:
            issue_lower = issue.lower()
            if issue_lower in self.valid_privacy_issues:
                valid_issues.append(issue_lower)
            else:
                unknown_issues.append(issue)

        return valid_issues, unknown_issues

    def _calculate_category_scores(self, valid_issues: List[str]) -> Dict[str, float]:
        """
        Calculate scores for all parent categories based on found issues.

        Args:
            valid_issues: List of validated privacy issues (lowercase)

        Returns:
            Dictionary mapping each parent category to its score (1.0 = best, 0.0 = worst)
        """
        # Initialize scores for all categories
        category_scores = {category: 1.0 for category in self.all_parent_categories}

        # Group valid issues by their parent categories
        issues_by_category: Dict[str, List[str]] = {}
        for item in valid_issues:
            # Split the item into parent issue and privacy issue
            if ':' not in item:
                print(f"Warning: Invalid issue format '{item}'. Skipping.")
                continue
            parent_issue, privacy_issue = map(str.strip, item.split(':', 1))

            # Ensure the parent issue exists in our category mapping
            if parent_issue not in self.all_parent_categories:
                print(f"Warning: Parent category '{parent_issue}' not recognized. Skipping.")
                continue

            # Add the privacy issue to the corresponding parent category
            if parent_issue not in issues_by_category:
                issues_by_category[parent_issue] = []
            issues_by_category[parent_issue].append(privacy_issue.lower())

        # Calculate score for each category that has issues
        for category, found_issues in issues_by_category.items():
            possible_issues = self.issues_by_category[category]
            if possible_issues:  # Avoid division by zero
                category_scores[category] = 1.0 - (len(found_issues) / len(possible_issues))

        return category_scores

    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate overall score as weighted average of category scores."""
        total_weight = sum(self.category_weights[cat] for cat in category_scores.keys())
        if total_weight == 0:
            return 1.0

        weighted_sum = sum(
            score * self.category_weights[category]
            for category, score in category_scores.items()
        )
        return weighted_sum / total_weight

    def _get_grade(self, score: float) -> Grade:
        """Convert numerical score to letter grade using grade boundaries."""
        for threshold, grade in sorted(self.grade_boundaries.items(), reverse=True):
            if score >= threshold:
                return grade
        return Grade.F

    def _restore_original_case(self, issues: List[str]) -> List[str]:
        """Restore the original case of issues using the case mapping."""
        return [self.case_mapping.get(issue, issue) for issue in issues]

    def grade_privacy_issues(self, privacy_issues: List[str]) -> Optional[PrivacyReport]:
        """
        Grade a list of privacy issues and generate a comprehensive report.

        Args:
            privacy_issues: List of specific privacy issues found

        Returns:
            PrivacyReport if at least some issues are valid, None if all issues are unknown
        """

        # Initialize issues grouped by category
        issues_by_category: Dict[str, List[str]] = {}

        # Split each issue into parent issue and privacy issue
        for issue in privacy_issues:
            if ':' not in issue:
                print(f"Warning: Invalid issue format '{issue}'. Skipping.")
                continue
            parent_issue, privacy_issue = map(str.strip, issue.split(':', 1))

            # Ensure the parent issue exists
            if parent_issue not in self.all_parent_categories:
                print(f"Warning: Parent category '{parent_issue}' not recognized. Skipping.")
                continue

            # Add the privacy issue to the corresponding category
            if parent_issue not in issues_by_category:
                issues_by_category[parent_issue] = []
            issues_by_category[parent_issue].append(privacy_issue.lower())

        # Calculate scores for all categories
        category_scores = self._calculate_category_scores(privacy_issues)

        # Calculate grades for each parent category
        category_grades = {}
        for category in self.all_parent_categories:
            score = category_scores[category]
            grade = self._get_grade(score)

            found_issues = issues_by_category.get(category, [])
            category_grades[category] = {
                "grade": grade.value,
                "score": round(score * 100, 2),
                "privacy_issues_found": self._restore_original_case(found_issues),
                "total_possible_issues": len(self.issues_by_category[category]),
                "category_weight": self.category_weights[category]
            }

        # Calculate overall weighted score and grade
        overall_score = self._calculate_overall_score(category_scores)
        overall_grade = self._get_grade(overall_score)

        # Identify worst parent categories (top 5 categories with issues found)
        worst_categories = sorted(
            [
                {
                    "parent_category": category,
                    "grade": data["grade"],
                    "score": data["score"],
                    "privacy_issues_found": data["privacy_issues_found"],
                    "total_possible_issues": data["total_possible_issues"],
                    "category_weight": data["category_weight"]
                }
                for category, data in category_grades.items()
                if len(data["privacy_issues_found"]) > 0
            ],
            key=lambda x: x["score"]
        )[:5]

        return PrivacyReport(
            overall_grade=overall_grade.value,
            overall_score=round(overall_score * 100, 2),
            parent_category_grades=category_grades,
            worst_parent_categories=worst_categories
        )
# Example usage
if __name__ == "__main__":
    mapping_df = pd.read_csv("mapping_df.csv")
    mapping_path = "/app/mapping_df.csv"
    # Load weights for grader
    category_weights = load_weights_from_csv('category_weights.csv')
    # Initialize the grader
    grader = PrivacyGrader(mapping_df, category_weights)

    # Example list of privacy issues found in a service
    # Get report
    found_issues = [
        'This service takes credit for your content',
        'If YOU OFFER suggestions to the service they become the owner of the ideas that you give them',
        'You maintain ownership of your content',
        'this service gives your personal data to third parties involved in its operation',
        'this service shares your personal data with third parties that are not essential to its operation',
        'YOU can delete your content from this service',
        'this service retains rights to your content even after you stop using your account',
        'the data retention period is kept to the minimum necessary for fulfilling its purposes',
        'the service may keep a secure anonymized record of your data for analytical purposes even after the data retention period',
        'no need to register',
        'not an issue_testing error reporting',
        'not an issue_testing error reporting2',
        'not an issue_testing error reporting3',
        'your personal data is used for limited purposes',
        'your personal information is used for many different purposes',
        'only aggregate data is given to third parties',
        'app required for this service requires broad device permissions',
        'your data is processed and stored in a country that is less friendly to user privacy protection',
        'your data may be processed and stored anywhere in the world',
        'your personal data will not be used for an automated decisionmaking',
        'your data is processed and stored in a country that is friendlier to user privacy protection',
        'private messages can be read'
    ]
    pdf_path = os.getenv("PDF_PATH", "/pdf_directory/default.pdf")
    project_id = "ac215-privasee"
    location_id = "us-central1"
    endpoint_id = "3317729057814085632"
    found_issues = process_pdf_privacy_issues(pdf_path, mapping_path, project_id, location_id, endpoint_id)
    report = grader.grade_privacy_issues(found_issues)

    if report:
        print(f"\nOverall Grade: {report.overall_grade}")
        print(f"Overall Score: {report.overall_score}%")

        if report.unknown_issues:
            print(f"\nUnknown Issues: {report.unknown_issues}")

        print("\nWorst Performing Parent Categories:")
        for category in report.worst_parent_categories:
            print(f"\n{category['parent_category']}:")
            print(f"Grade: {category['grade']}")
            print(f"Score: {category['score']}%")
            print("Privacy Issues Found:", category['privacy_issues_found'])
            print(f"Total Possible Issues: {category['total_possible_issues']}")