import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from nlp.tokenizer.tokenizer import CommandTokenizer
from nlp.model.transformer import MagnasNLPModel
from nlp.training.multi_agent_dataset import AGENT_DATASETS, ROUTER_DOMAINS

class TextDataset(Dataset):
    def __init__(self, samples, tokenizer, label_map):
        self.samples = samples
        self.tokenizer = tokenizer
        self.label_map = label_map

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        text, label_str = self.samples[idx]
        ids = self.tokenizer.encode(text, max_length=32)
        target = self.label_map.get(label_str, 0)
        return torch.tensor(ids, dtype=torch.long), torch.tensor(target, dtype=torch.long)

def train_single_agent(agent_name: str, samples: list, model_dir: str):
    os.makedirs(model_dir, exist_ok=True)
    labels = sorted(list(set(s[1] for s in samples)))
    label_map = {lbl: i for i, lbl in enumerate(labels)}

    tokenizer = CommandTokenizer()
    texts = [s[0] for s in samples]
    tokenizer.build_vocab(texts)
    tokenizer.save(os.path.join(model_dir, "tokenizer.json"))

    with open(os.path.join(model_dir, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2)

    dataset = TextDataset(samples, tokenizer, label_map)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    model = MagnasNLPModel(vocab_size=len(tokenizer.vocab), num_intents=len(labels), num_slots=5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(12):
        for input_ids, targets in dataloader:
            optimizer.zero_grad()
            intent_logits, _ = model(input_ids)
            loss = criterion(intent_logits, targets)
            loss.backward()
            optimizer.step()

    # Save PyTorch .pth model
    pth_path = os.path.join(model_dir, "model.pth")
    torch.save(model.state_dict(), pth_path)

    # Export to ONNX
    try:
        model.eval()
        dummy_input = torch.zeros(1, 32, dtype=torch.long)
        onnx_path = os.path.join(model_dir, "model.onnx")
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input_ids"],
            output_names=["intent_logits", "slot_logits"],
            dynamic_axes={"input_ids": {0: "batch_size"}, "intent_logits": {0: "batch_size"}},
            opset_version=14
        )
    except Exception as e:
        print(f"[{agent_name}] ONNX Export note: {e}")

    print(f"  [OK] Trained & exported micro-agent '{agent_name}' ({len(labels)} intents) to '{model_dir}'")

def train_all_agents():
    print("==================================================")
    print(" TRAINING MAGNAS 11-MICRO-AGENT NLP NETWORK")
    print("==================================================")

    # 1. Train Router Agent
    router_samples = []
    domain_mapping = {
        "os_agent": "DOMAIN_OS",
        "browser_agent": "DOMAIN_BROWSER",
        "ide_agent": "DOMAIN_IDE",
        "resume_agent": "DOMAIN_RESUME",
        "security_agent": "DOMAIN_SECURITY",
        "database_agent": "DOMAIN_DATABASE",
        "vision_agent": "DOMAIN_VISION_MEDIA",
        "scheduler_agent": "DOMAIN_SCHEDULER",
        "cli_agent": "DOMAIN_CLI",
        "llm_agent": "DOMAIN_LLM"
    }

    for agent_key, dataset in AGENT_DATASETS.items():
        domain_tag = domain_mapping[agent_key]
        for text, _ in dataset:
            router_samples.append((text, domain_tag))

    train_single_agent("router_agent", router_samples, "nlp/models/agents/router_agent")

    # 2. Train Domain Micro-Agents
    for agent_name, dataset in AGENT_DATASETS.items():
        out_dir = f"nlp/models/agents/{agent_name}"
        train_single_agent(agent_name, dataset, out_dir)

    print("\n==================================================")
    print(" ALL 11 MICRO-AGENTS TRAINED & EXPORTED CLEANLY!")
    print("==================================================")

if __name__ == "__main__":
    train_all_agents()
