import pytest
import torch
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from torch.utils.data import DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, AdamW
from models.modeling_functions import PrivacyDataset, collate_fn  # Replace 'modeling_functions' with actual module name

# Mock data for testing
@pytest.fixture
def mock_data():
    # Mock dataset to test basic data functions
    data = {
        "service": ["service1", "service2"],
        "full_text_clean": ["This is a sample privacy policy.", "Another privacy policy with more text."],
        "privacy_issue": [["issue1"], ["issue2", "issue3"]]
    }
    return pd.DataFrame(data)

@pytest.fixture
def binarized_labels(mock_data):
    # Unit test for label binarization
    mlb = MultiLabelBinarizer()
    labels = mlb.fit_transform(mock_data["privacy_issue"])
    return labels, mlb

@pytest.fixture
def train_test_split_data(mock_data, binarized_labels):
    # Provides data for integration testing of dataset split and preprocessing
    labels, _ = binarized_labels
    full_texts = mock_data["full_text_clean"].tolist()
    return full_texts, labels

# Mock Tokenizer to return real tensors
@pytest.fixture
def mock_tokenizer():
    # Mock tokenizer for unit and integration tests
    class MockTokenizer:
        def __init__(self):
            self.pad_token_id = 0
            
        def encode(self, text, add_special_tokens=False):
            return [1] * len(text.split())
        
        def __call__(self, text, max_length, padding, truncation, return_tensors):
            length = min(len(text.split()), max_length)
            input_ids = torch.tensor([[1] * length + [0] * (max_length - length)], dtype=torch.long)
            attention_mask = torch.tensor([[1] * length + [0] * (max_length - length)], dtype=torch.long)
            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask
            }
            
    return MockTokenizer()

@pytest.fixture
def setup_privacy_dataset(train_test_split_data, mock_tokenizer):
    # Integration fixture for creating PrivacyDataset instance
    texts, labels = train_test_split_data
    return PrivacyDataset(texts, labels, mock_tokenizer, max_len=10)

# Unit test: Checking dataset length
def test_privacy_dataset_len(setup_privacy_dataset):
    assert len(setup_privacy_dataset) == 2  # Expect 2 items in dataset

# Unit test: Testing text chunking functionality
def test_privacy_dataset_chunk_text(mock_tokenizer):
    dataset = PrivacyDataset(
        texts=["This is a sample privacy policy that exceeds the maximum length for testing chunking functionality."],
        labels=[[1, 0, 1]],
        tokenizer=mock_tokenizer,
        max_len=5  # Setting a small max_len for easy chunking
    )
    chunks = dataset.chunk_text(dataset.texts[0])
    assert len(chunks) > 1  # Should create multiple chunks
    for chunk in chunks:
        assert len(chunk.split()) <= dataset.max_len  # Each chunk should be within max_len

# Integration test: Ensuring getitem method works with mock tokenizer and collates chunks correctly
def test_privacy_dataset_getitem(mock_tokenizer):
    dataset = PrivacyDataset(
        texts=["Sample text for testing.", "Another sample text that is slightly longer for testing."],
        labels=[[1, 0], [0, 1]],
        tokenizer=mock_tokenizer,
        max_len=10
    )
    item = dataset[0]
    assert isinstance(item, list)  # Each item should return a list of dictionaries for each chunk
    for chunk in item:
        assert "input_ids" in chunk
        assert "attention_mask" in chunk
        assert "labels" in chunk
        assert chunk["input_ids"].shape[0] == dataset.max_len  # Should be padded to max_len

# Integration test: Testing padding functionality within collate function
def test_collate_fn_padding(setup_privacy_dataset):
    # Create a dataloader to test collate_fn
    dataloader = DataLoader(setup_privacy_dataset, batch_size=2, collate_fn=collate_fn)
    batch = next(iter(dataloader))
    
    # Check that the collate function returns properly padded sequences
    assert "input_ids" in batch
    assert "attention_mask" in batch
    assert "labels" in batch
    assert batch["input_ids"].shape[0] == 2  # Batch size
    assert batch["attention_mask"].shape[0] == 2
    assert batch["labels"].shape[0] == 2

# Unit test: Ensuring empty text handling within dataset
def test_empty_text(mock_tokenizer):
    # Test handling of empty text
    dataset = PrivacyDataset(
        texts=[""],
        labels=[[1, 0, 1]],
        tokenizer=mock_tokenizer,
        max_len=5
    )
    item = dataset[0]
    assert isinstance(item, list)
    assert len(item) == 0  # Expect 0 chunks for an empty text

# Unit test: Ensuring long text is chunked properly within dataset
def test_long_text(mock_tokenizer):
    # Test handling of very long text
    long_text = " ".join(["word"] * 1000)  # Create a long text
    dataset = PrivacyDataset(
        texts=[long_text],
        labels=[[1, 1, 0]],
        tokenizer=mock_tokenizer,
        max_len=50  # Set a small max_len for multiple chunks
    )
    item = dataset[0]
    assert isinstance(item, list)
    assert len(item) > 1  # Long text should be chunked into multiple items