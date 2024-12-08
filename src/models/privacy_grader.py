import os
import pandas as pd
from google.cloud import storage
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
# from get_issues import process_pdf_privacy_issues
from .get_issues import *
def get_storage_client():
    """Returns a Google Cloud Storage client."""
    return storage.Client()

storage_client = get_storage_client()
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
class PrivacyCategoryReport:
    """Detailed report for a privacy category."""
    parent_category: str
    grade: str
    score: float
    good_issues: List[str]
    neutral_issues: List[str]
    bad_issues: List[str]
    total_possible_issues: int
    category_weight: float


@dataclass
class PrivacyReport:
    """Container for privacy grading results."""
    overall_grade: str
    overall_score: float
    parent_category_grades: Dict[str, PrivacyCategoryReport]
    worst_parent_categories: List[PrivacyCategoryReport]
    unknown_issues: Optional[List[str]] = None


class PrivacyGrader:
    def __init__(self, mapping_df: pd.DataFrame, category_weights: Dict[str, float] = None):
        # Store mapping DataFrame and create set of valid issues (converted to lowercase)
        self.mapping_df = mapping_df.copy()
        self.mapping_df['privacy_issue'] = self.mapping_df['privacy_issue'].str.lower()
        self.valid_privacy_issues = set(self.mapping_df['privacy_issue'].unique())

        # Classification weights
        self.classification_weights = {
            'blocker': -2.0,  # Much stronger penalty
            'bad': -0.7,  # Stronger penalty
            'neutral': 0.0,  # no impact
            'good': 0.1  # positive impact
        }

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
            0.95: Grade.A,
            0.85: Grade.B,
            0.75: Grade.C,
            0.65: Grade.D,
            # Below 65% = F
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
            if ':' not in issue:
                unknown_issues.append(issue)
                continue

            # Split and get the actual issue part after the colon
            _, privacy_issue = map(str.strip, issue.split(':', 1))
            issue_lower = privacy_issue.lower()

            if issue_lower in self.valid_privacy_issues:
                valid_issues.append(issue)  # Keep the original formatted string
            else:
                unknown_issues.append(issue)

        return valid_issues, unknown_issues
    def _calculate_category_scores(self, valid_issues: List[str]) -> Dict[str, float]:
        """Calculate scores based on issue classifications with stricter penalties."""
        category_scores = {category: 1.0 for category in self.all_parent_categories}

        issues_by_category: Dict[str, List[str]] = {}
        for item in valid_issues:
            if ':' not in item:
                continue
            parent_issue, privacy_issue = map(str.strip, item.split(':', 1))

            if parent_issue not in self.all_parent_categories:
                continue

            if parent_issue not in issues_by_category:
                issues_by_category[parent_issue] = []
            issues_by_category[parent_issue].append(privacy_issue.lower())

        for category in self.all_parent_categories:
            found_issues = issues_by_category.get(category, [])
            if not found_issues:
                continue

            base_score = 1.0
            issue_classifications = []

            # Get classifications for each issue
            for issue in found_issues:
                classification = self.mapping_df[
                    (self.mapping_df['parent_issue'] == category) &
                    (self.mapping_df['privacy_issue'].str.lower() == issue.lower())
                    ]['classification'].iloc[0]
                issue_classifications.append(classification)

                # Apply impact from classification
                base_score += self.classification_weights[classification]

            # Count types of issues
            blocker_count = issue_classifications.count('blocker')
            bad_count = issue_classifications.count('bad')
            good_count = issue_classifications.count('good')

            # Enhanced penalty rules
            if blocker_count > 0:
                # Severe penalty for any blockers
                base_score = min(base_score, 0.3)
            elif bad_count > 0:
                # Cap score if there are any bad issues
                base_score = min(base_score, 0.7)

            # Reduce the minimum score for all good issues
            if len(found_issues) == good_count:
                base_score = max(base_score, 0.7)

            # Apply category weight
            score = base_score * self.category_weights[category]

            # Ensure score stays within bounds
            category_scores[category] = max(min(score, 1.0), 0.0)

        return category_scores


    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate overall score as weighted average of category scores."""
        total_weight = sum(self.category_weights[cat] for cat in category_scores.keys())

        if total_weight == 0:
            return 0.0

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
        Grade privacy issues and generate a comprehensive report with issues grouped by classification.
        """
        valid_issues, unknown_issues = self._validate_issues(privacy_issues)

        if not valid_issues and not unknown_issues:
            print("No valid privacy issues found.")
            return None

        # Group issues by category and classification
        issues_by_category: Dict[str, Dict[str, List[str]]] = {}

        for issue in valid_issues:
            if ':' not in issue:
                continue

            parent_issue, privacy_issue = map(str.strip, issue.split(':', 1))

            if parent_issue not in self.all_parent_categories:
                continue

            if parent_issue not in issues_by_category:
                issues_by_category[parent_issue] = {
                    'good': [],
                    'neutral': [],
                    'bad': []  # Will include both bad and blocker
                }

            # Get classification from mapping_df
            classification = self.mapping_df[
                (self.mapping_df['parent_issue'] == parent_issue) &
                (self.mapping_df['privacy_issue'].str.lower() == privacy_issue.lower())
                ]['classification'].iloc[0]

            # Group into good, neutral, or bad (including blockers)
            if classification == 'good':
                issues_by_category[parent_issue]['good'].append(privacy_issue)
            elif classification == 'neutral':
                issues_by_category[parent_issue]['neutral'].append(privacy_issue)
            else:  # 'bad' or 'blocker'
                issues_by_category[parent_issue]['bad'].append(privacy_issue)

        # Calculate scores
        category_scores = self._calculate_category_scores(valid_issues)

        # Create detailed category reports
        category_grades = {}
        for category in self.all_parent_categories:
            score = category_scores[category]
            grade = self._get_grade(score)

            category_grades[category] = PrivacyCategoryReport(
                parent_category=category,
                grade=grade.value,
                score=round(score * 100, 2),
                good_issues=issues_by_category.get(category, {}).get('good', []),
                neutral_issues=issues_by_category.get(category, {}).get('neutral', []),
                bad_issues=issues_by_category.get(category, {}).get('bad', []),
                total_possible_issues=len(self.issues_by_category[category]),
                category_weight=self.category_weights[category]
            )

        # Calculate overall score and grade
        overall_score = self._calculate_overall_score(category_scores)
        overall_grade = self._get_grade(overall_score)

        # Identify worst categories (those with bad issues)
        worst_categories = sorted(
            [
                report for category, report in category_grades.items()
                if report.bad_issues
            ],
            key=lambda x: x.score
        )[:5]

        return PrivacyReport(
            overall_grade=overall_grade.value,
            overall_score=round(overall_score * 100, 2),
            parent_category_grades=category_grades,
            worst_parent_categories=worst_categories,
            unknown_issues=unknown_issues if unknown_issues else None
        )

    def save_grade_to_csv(service_name: str, grade: str, csv_path: str = 'privacy_grades.csv') -> None:
        """
        Save or update privacy grade for a service in CSV file.
        If service already exists, preserve the existing grade.

        Args:
            service_name: Name of the service being graded
            grade: Privacy grade (A-F)
            csv_path: Path to CSV file storing grades
        """
        try:
            # Try to read existing CSV file
            try:
                df = pd.read_csv(csv_path)
            except FileNotFoundError:
                # If file doesn't exist, create new DataFrame
                df = pd.DataFrame(columns=['service_name', 'grade'])

            # Check if service already exists
            if service_name not in df['service_name'].values:
                # Add new row
                new_row = pd.DataFrame({
                    'service_name': [service_name],
                    'grade': [grade]
                })
                df = pd.concat([df, new_row], ignore_index=True)

                # Save updated DataFrame
                df.to_csv(csv_path, index=False)
                print(f"Added grade {grade} for {service_name} to {csv_path}")
            else:
                print(f"Service {service_name} already exists in {csv_path}. Preserving existing grade.")

        except Exception as e:
            print(f"Error saving grade to CSV: {str(e)}")

# Example usage
if __name__ == "__main__":
    # mapping parent to child issues
    mapping_df = pd.read_csv("mapping_df.csv")
    mapping_path = "/app/mapping_df.csv"
    # Load weights for grader
    category_weights = load_weights_from_csv('category_weights.csv')
    # Initialize the grader
    grader = PrivacyGrader(mapping_df, category_weights)

    # TEST1: Example list of privacy issues found in a service
    found_issues = [
        'Ownership: This service takes credit for your content',
        'Ownership: If YOU OFFER suggestions to the service they become the owner of the ideas that you give them',
        'Ownership: You maintain ownership of your content',
        'Third Parties: this service gives your personal data to third parties involved in its operation',
        'Third Parties: this service shares your personal data with third parties that are not essential to its operation',
        'Right to Leave The Service: YOU can delete your content from this service',
        'Right to Leave The Service: this service retains rights to your content even after you stop using your account',
        'Right to Leave The Service: the data retention period is kept to the minimum necessary for fulfilling its purposes',
        'Right to Leave The Service: the service may keep a secure anonymized record of your data for analytical purposes even after the data retention period',
        'Right to Leave The Service: no need to register',
        'not an issue_testing error reporting',
        'not an issue_testing error reporting2',
        # 'not an issue_testing error reporting3' - not in mapping
        'Personal Data: your personal data is used for limited purposes',
        'Personal Data: your personal information is used for many different purposes',
        'Personal Data: only aggregate data is given to third parties',
        'Personal Data: app required for this service requires broad device permissions',
        'Personal Data: your data is processed and stored in a country that is less friendly to user privacy protection',
        'Personal Data: your data may be processed and stored anywhere in the world',
        'Personal Data: your personal data will not be used for an automated decisionmaking',
        'Personal Data: your data is processed and stored in a country that is friendlier to user privacy protection',
        'Personal Data: private messages can be read'
    ]
    # report = grader.grade_privacy_issues(found_issues)

    # # TEST2 using the pdf extraction process
    pdf_path = os.getenv("PDF_PATH", "pdf_directory/amazon.pdf")  # pdf to analyze
    csv_path = "mapping_df.csv"  # mapping pdf for issues
    project_id = "ac215-privasee"
    location_id = "us-central1"  # Your region
    endpoint_id = "3504346967373250560"  # Your endpoint ID

    print(f"Processing file: {pdf_path}")
    print(f"Using mapping: {csv_path}")
    print(f"Project ID: {project_id}")
    print(f"Location: {location_id}")
    print(f"Endpoint ID: {endpoint_id}")

    found_issues= process_pdf_privacy_issues(
        pdf_path=pdf_path,
        csv_path=csv_path,
        project_id=project_id,
        location_id=location_id,
        endpoint_id=endpoint_id
    )

    grader = PrivacyGrader(mapping_df, category_weights)
    report = grader.grade_privacy_issues(found_issues)
    if report:
        # print(f"\n Report card for {service}")
        print(f"\nOverall Grade: {report.overall_grade}")
        print(f"Overall Score: {report.overall_score}%")

        if report.unknown_issues:
            print(f"\nUnknown Issues: {report.unknown_issues}")

        print("\nWorst Performing Categories:")
        for category in report.worst_parent_categories:
            print(f"\nCategory: {category.parent_category}")  # Added this line
            print(f"Grade: {category.grade} ({category.score}%)")
            if category.bad_issues:
                print("Severe Privacy Issues:", category.bad_issues)
            if category.neutral_issues:
                print("Neutral Privacy Issues:", category.neutral_issues)
            if category.good_issues:
                print("Good Privacy Practices:", category.good_issues)
            print(f"Total Possible Issues: {category.total_possible_issues}")
        # save privacy grade to csv
        # report.save_grade_to_csv(service_name, report.overall_grade)
