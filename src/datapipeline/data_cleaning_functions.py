import re
from bs4 import BeautifulSoup

# Funtions to clean the data
def remove_html_tags(text):
    """Remove HTML tags using BeautifulSoup."""
    soup = BeautifulSoup(text, "html.parser")
    cleaned_text = soup.get_text()
    return cleaned_text
def remove_text_in_brackets(text):
    """Remove text within angle brackets."""
    return re.sub(r'<[^>]*>', '', text)

def remove_urls_and_emails(text):
    """Remove URLs and email addresses."""
    #remove urls
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove emails
    text = re.sub(r'\S*@\S*\s?', '', text)
    return text

def remove_control_characters(text):
    """Remove non-printable and control characters."""
    # Replace common control characters with space
    text = re.sub(r'[\r\n\t\f\v]', ' ', text)
    # Remove remaining control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return text

def remove_special_characters(text, remove_digits=False):
    """Remove special characters, optionally including digits."""
    pattern = r'[^a-zA-Z0-9\s]' if not remove_digits else r'[^a-zA-Z\s]'
    text = re.sub(pattern, '', text)
    return text

def preprocess_text(text):
    """Apply all preprocessing steps to the text."""
    text = remove_text_in_brackets(text)
    text = remove_urls_and_emails(text)
    text = remove_control_characters(text)
    text = remove_special_characters(text)
    return text