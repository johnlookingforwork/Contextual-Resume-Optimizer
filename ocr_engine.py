import pytesseract
from PIL import Image

def extract_text_from_image(image_path: str) -> str:
    """Uses Tesseract OCR to extract text from a screenshot."""
    # Open the screenshot using PIL (Python Imaging Library)
    img = Image.open(image_path)
    
    # Perform OCR on the image
    raw_text = pytesseract.image_to_string(img)
    
    return raw_text

if __name__ == "__main__":
    # Test it with your screenshot
    text = extract_text_from_image("data/job_screenshot.png")
    print("--- OCR Extracted Text ---")
    print(text[:500])