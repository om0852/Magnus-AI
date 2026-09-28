import os
from typing import Dict, Any, List

def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """OCR abstraction layer for screen understanding."""
    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image file not found: {image_path}", "text": ""}
    
    # Simple fallback check for Tesseract OCR / PIL
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return {"success": True, "text": text.strip(), "engine": "pytesseract"}
    except Exception as e:
        return {
            "success": False,
            "engine": "none",
            "text": "[OCR Engine not initialized: pytesseract or tesseract binary missing]",
            "error": str(e)
        }
