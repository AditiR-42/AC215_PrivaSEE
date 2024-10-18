import torch
from torch.utils.data import Dataset, DataLoader

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
