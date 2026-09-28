import os
import json
from nlp.tokenizer.tokenizer import CommandTokenizer, FIXED_VOCAB_SIZE
from nlp.training.dataset_generator import INTENTS, generate_dataset, save_dataset

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from nlp.model.transformer import MagnasNLPModel
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def train_model(output_dir: str = "nlp/models/magnas-nlp", epochs: int = 5):
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating training dataset...", flush=True)
    raw_data = generate_dataset(num_samples=10000)
    
    tokenizer = CommandTokenizer()
    texts = [d["text"] for d in raw_data]
    tokenizer.build_vocab(texts)
    tokenizer.save(os.path.join(output_dir, "tokenizer.json"))
    
    intent_map = {intent: i for i, intent in enumerate(INTENTS)}
    with open(os.path.join(output_dir, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(intent_map, f, indent=2)

    if not HAS_TORCH:
        print("[Notice] PyTorch is not installed in current environment. Built tokenizer & label vocabulary for rule-based engine.", flush=True)
        return None, tokenizer

    class CommandDataset(Dataset):
        def __init__(self, samples, tokenizer, max_length=32):
            self.samples = samples
            self.tokenizer = tokenizer
            self.max_length = max_length
            self.intent2id = {intent: i for i, intent in enumerate(INTENTS)}

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, idx):
            sample = self.samples[idx]
            input_ids = self.tokenizer.encode(sample["text"], max_length=self.max_length)
            intent_id = self.intent2id.get(sample["intent"], self.intent2id["UNKNOWN"])
            return torch.tensor(input_ids, dtype=torch.long), torch.tensor(intent_id, dtype=torch.long)

    dataset = CommandDataset(raw_data, tokenizer)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    model = MagnasNLPModel(
        vocab_size=FIXED_VOCAB_SIZE,
        num_intents=len(INTENTS),
        num_slots=10
    )
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    print("Training PyTorch Transformer model...", flush=True)
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for input_ids, intent_targets in dataloader:
            optimizer.zero_grad()
            intent_logits, _ = model(input_ids)
            loss = criterion(intent_logits, intent_targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs} - Loss: {total_loss / len(dataloader):.4f}", flush=True)

    torch.save(model.state_dict(), os.path.join(output_dir, "model.pth"))
    print(f"Model saved to '{output_dir}/model.pth'", flush=True)
    return model, tokenizer

if __name__ == "__main__":
    train_model()
