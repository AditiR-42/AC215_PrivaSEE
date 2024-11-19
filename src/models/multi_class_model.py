datapath='gs://legal-terms-data/tosdr-data/modeling/df_mod_v1.csv'
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from transformers import BertForSequenceClassification, AdamW
from transformers import BertTokenizer
df = pd.read_csv(datapath)
### Define the labels and design matrix
# oour modeling dataframe
mod_df= df.groupby(['service','full_text_clean'], as_index=False)['privacy_issue'].agg(list)
mod_df.shape, mod_df.service.nunique(),mod_df.full_text_clean.nunique()
mod_df.head()
services = mod_df['service'].tolist()
full_texts = mod_df['full_text_clean'].tolist()
len(services), len(full_texts)
#Multi-label binarization
mlb = MultiLabelBinarizer()
labels = mlb.fit_transform(mod_df["privacy_issue"])
# print(f"Classes: {mlb.classes_}")
print(f"Encoded Labels Shape: {labels.shape}")  # Shape will be (num_samples, num_issues)
#check on number of privacy issues per text
row_sums = np.sum(labels , axis=1)
# Convert to a DataFrame for better readability (optional)
row_sums_df = pd.DataFrame(row_sums, columns=['Privacy Issue Count'])
row_sums_df.head()
#Train test split
train_texts, val_texts, train_labels, val_labels = train_test_split(full_texts, labels, test_size=0.3, random_state=42)
print(len(train_texts), len(train_labels), len(val_texts), len(val_labels))
# Set up multi -label classification
# Load BERT tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
# Load pre-trained BERT model with correct output size
num_issues = len(mlb.classes_)
print('number of classes to classify: ', num_issues)
model = BertForSequenceClassification.from_pretrained("bert-base-uncased",
                                                      num_labels=num_issues,
                                                      problem_type="multi_label_classification")
# Loss function and optimizer
loss_fn = torch.nn.BCEWithLogitsLoss()
optimizer = AdamW(model.parameters(), lr=2e-5, eps=1e-8)

# Device configuration
# device = torch.device("cuda")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
# Data Prep for Pytorch
class PrivacyDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def chunk_text(self, text):
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            token_length = len(self.tokenizer.encode(word, add_special_tokens=False))
            if current_length + token_length > self.max_len:
                chunks.append(" ".join(current_chunk))  # Join words into a chunk
                current_chunk = [word]  # Start a new chunk with the current word
                current_length = token_length  # Reset current length for the new chunk
            else:
                current_chunk.append(word)
                current_length += token_length

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def __getitem__(self, idx):
        text = self.texts[idx]
        labels = self.labels[idx]

        # Chunk the text if it exceeds max_len
        chunked_texts = self.chunk_text(text)

        inputs = []
        for chunk in chunked_texts:
            # Tokenize and encode each chunk
            encoded_chunk = self.tokenizer(
                chunk, max_length=self.max_len, padding="max_length", truncation=True, return_tensors="pt"
            )
            inputs.append({
                "input_ids": encoded_chunk["input_ids"].squeeze(0),
                "attention_mask": encoded_chunk["attention_mask"].squeeze(0),
                "labels": torch.tensor(labels, dtype=torch.float)  # Move label tensor creation here
            })

        # Instead of returning a list of dicts, we return the chunks
        return inputs  # This will return a list of dictionaries


def collate_fn(batch):
    # Flatten the list of inputs from each sample in the batch
    input_ids = []
    attention_masks = []
    labels = []

    for sample in batch:
        for item in sample:  # Loop through each input of the sample
            input_ids.append(item['input_ids'])
            attention_masks.append(item['attention_mask'])
            labels.append(item['labels'])

    # Pad sequences to the maximum length in the batch
    input_ids = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True)
    attention_masks = torch.nn.utils.rnn.pad_sequence(attention_masks, batch_first=True)
    labels = torch.stack(labels)  # Stack labels into a tensor

    return {
        "input_ids": input_ids,
        "attention_mask": attention_masks,
        "labels": labels
    }

train_dataset = PrivacyDataset(train_texts,train_labels, tokenizer)
train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True, collate_fn=collate_fn)
test_dataset = PrivacyDataset(val_texts,val_labels, tokenizer)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False, collate_fn=collate_fn)
### Training Loop
def train(model, dataloader, optimizer, loss_fn, epochs=3):
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch in dataloader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            # Forward pass
            outputs = model(input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, labels)

            # Backward pass and optimization
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch + 1}, Loss: {avg_loss:.4f}")
torch.cuda.empty_cache()  # Clears unused cache memory
# Train the model
train(model, train_loader, optimizer, loss_fn)
