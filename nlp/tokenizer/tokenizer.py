import json
import re
from typing import List, Dict, Any, Tuple

FIXED_VOCAB_SIZE = 2500

class CommandTokenizer:
    """Specialized fixed-vocabulary tokenizer for Magnas NLP intents and entity slots."""

    def __init__(self, vocab: List[str] = None):
        self.pad_token = "<PAD>"
        self.unk_token = "<UNK>"
        
        if vocab is None:
            self.vocab = [self.pad_token, self.unk_token] + [f"<RESERVED_{i}>" for i in range(FIXED_VOCAB_SIZE - 2)]
        else:
            if len(vocab) < FIXED_VOCAB_SIZE:
                vocab = vocab + [f"<RESERVED_{i}>" for i in range(FIXED_VOCAB_SIZE - len(vocab))]
            else:
                vocab = vocab[:FIXED_VOCAB_SIZE]
            self.vocab = vocab

        self.token2id = {t: i for i, t in enumerate(self.vocab)}
        self.id2token = {i: t for i, t in enumerate(self.vocab)}

    def build_vocab(self, texts: List[str]):
        tokens_set = set()
        for text in texts:
            words = self._tokenize(text)
            tokens_set.update(words)
        
        sorted_tokens = sorted(list(tokens_set))
        new_vocab = [self.pad_token, self.unk_token] + sorted_tokens[:FIXED_VOCAB_SIZE - 2]
        if len(new_vocab) < FIXED_VOCAB_SIZE:
            new_vocab += [f"<RESERVED_{i}>" for i in range(FIXED_VOCAB_SIZE - len(new_vocab))]

        self.vocab = new_vocab
        self.token2id = {t: i for i, t in enumerate(self.vocab)}
        self.id2token = {i: t for i, t in enumerate(self.vocab)}

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        words = re.findall(r"\w+|[^\w\s]", text)
        return words

    def encode(self, text: str, max_length: int = 32) -> List[int]:
        tokens = self._tokenize(text)
        token_ids = [self.token2id.get(t, self.token2id[self.unk_token]) for t in tokens[:max_length]]
        padding = [self.token2id[self.pad_token]] * (max_length - len(token_ids))
        return token_ids + padding

    def decode(self, ids: List[int]) -> List[str]:
        return [self.id2token.get(i, self.unk_token) for i in ids if i != self.token2id[self.pad_token]]

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"vocab": self.vocab}, f, indent=2)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(vocab=data["vocab"])
