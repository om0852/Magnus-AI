import torch
import torch.nn as nn
from nlp.tokenizer.tokenizer import FIXED_VOCAB_SIZE

class MagnasNLPModel(nn.Module):
    """
    Dual-head Transformer Encoder model for computer control intents & entity slot filling.
    Head 1: Intent classification over N intents
    Head 2: Slot/Entity classification over M slot tags per token
    """

    def __init__(self, vocab_size: int = FIXED_VOCAB_SIZE, num_intents: int = 15, num_slots: int = 10, d_model: int = 128, nhead: int = 4, num_layers: int = 2):
        super(MagnasNLPModel, self).__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_encoder = nn.Parameter(torch.zeros(1, 64, d_model))
        
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=256, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.intent_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, num_intents)
        )
        
        self.slot_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, num_slots)
        )

    def forward(self, input_ids):
        seq_len = input_ids.size(1)
        x = self.embedding(input_ids) + self.pos_encoder[:, :seq_len, :]
        encoded = self.transformer_encoder(x)
        
        # Pooled mean output for intent
        pooled = torch.mean(encoded, dim=1)
        intent_logits = self.intent_head(pooled)
        
        # Token-level slot predictions
        slot_logits = self.slot_head(encoded)
        
        return intent_logits, slot_logits
