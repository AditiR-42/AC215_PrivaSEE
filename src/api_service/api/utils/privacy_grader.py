import pandas as pd
from typing import List, Dict


class PrivacyGrader:
    def __init__(self, csv_path: str):
        """
        Initialize PrivacyGrader with a path to a CSV file.

        Args:
            csv_path (str): Path to the CSV file containing `parent_issue` and `privacy_issue` columns.
        """
        self.mapping_df = pd.read_csv(csv_path)
        self.mapping_df['privacy_issue'] = self.mapping_df['privacy_issue'].str.lower()
        self.valid_privacy_issues = set(self.mapping_df['privacy_issue'].unique())
        self.all_parent_categories = set(self.mapping_df['parent_issue'].unique())
        self.issues_by_category = self._create_category_mapping()
        self.grade_boundaries = {
            0.8: "A", 
            0.6: "B", 
            0.4: "C", 
            0.2: "D"
        }

    def _create_category_mapping(self) -> Dict[str, List[str]]:
        """Map parent categories to their child issues."""
        return {
            category: self.mapping_df[self.mapping_df['parent_issue'] == category]['privacy_issue'].tolist()
            for category in self.all_parent_categories
        }

    def grade_privacy_issues(self, privacy_issues: List[str]) -> Dict:
        """
        Grade the privacy issues.

        Args:
            privacy_issues (List[str]): List of privacy issues in the format "parent_issue: privacy_issue".

        Returns:
            Dict: Grading report containing the overall grade, overall score, and category scores.
        """
        # Initialize category scores to perfect (1.0)
        category_scores = {category: 1.0 for category in self.all_parent_categories}
        issues_by_category = {}

        # Process found issues
        for issue in privacy_issues:
            if ':' not in issue:
                continue
            parent_issue, privacy_issue = map(str.strip, issue.split(':', 1))
            if parent_issue in self.all_parent_categories:
                issues_by_category.setdefault(parent_issue, []).append(privacy_issue.lower())

        # Calculate scores for each category
        for category, found_issues in issues_by_category.items():
            possible_issues = self.issues_by_category[category]
            if possible_issues:
                category_scores[category] = 1.0 - len(found_issues) / len(possible_issues)

        # Calculate the overall score
        overall_score = sum(category_scores.values()) / len(category_scores)
        overall_grade = next(
            (grade for threshold, grade in sorted(self.grade_boundaries.items(), reverse=True) if overall_score >= threshold),
            "F"
        )

        return {
            "overall_grade": overall_grade,
            "overall_score": round(overall_score * 100, 2),
            "category_scores": category_scores,
        }