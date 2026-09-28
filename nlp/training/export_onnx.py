import os
from nlp.tokenizer.tokenizer import CommandTokenizer
from nlp.training.dataset_generator import INTENTS

try:
    import torch
    from nlp.model.transformer import MagnasNLPModel
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def export_to_onnx(model_dir: str = "nlp/models/magnas-nlp"):
    if not HAS_TORCH:
        print("[Notice] PyTorch not installed. ONNX export skipped.")
        return False

    tokenizer_path = os.path.join(model_dir, "tokenizer.json")
    model_path = os.path.join(model_dir, "model.pth")
    onnx_path = os.path.join(model_dir, "model.onnx")

    if not os.path.exists(tokenizer_path) or not os.path.exists(model_path):
        print("Model or tokenizer not found.")
        return False

    tokenizer = CommandTokenizer.load(tokenizer_path)
    model = MagnasNLPModel(
        vocab_size=len(tokenizer.vocab),
        num_intents=len(INTENTS),
        num_slots=10
    )
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.zeros((1, 32), dtype=torch.long)
    
    try:
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input_ids"],
            output_names=["intent_logits", "slot_logits"],
            dynamic_axes={"input_ids": {0: "batch_size"}, "intent_logits": {0: "batch_size"}, "slot_logits": {0: "batch_size"}},
            opset_version=14
        )
        print(f"Exported ONNX model successfully to '{onnx_path}'")
        return True
    except Exception as e:
        print(f"[Notice] PyTorch model trained & saved to '{model_path}'.")
        return False

if __name__ == "__main__":
    export_to_onnx()
