"""
Test script for Firebase Vision API functions.
Run with: python manage.py shell < devices/test_firebase_vision.py
Or: python manage.py shell, then import and test functions
"""
from devices.firebase_vision import (
    detect_mail_type,
    read_text,
    detect_logos,
    estimate_size,
    analyze_mail
)
import base64

# Example usage (replace with actual base64 image)
def test_functions():
    """Test all Firebase Vision functions"""
    
    # Example: Load a test image
    # with open('test_mail_image.jpg', 'rb') as f:
    #     base64_image = base64.b64encode(f.read()).decode()
    
    # For testing, use a placeholder
    print("Firebase Vision API Test")
    print("=" * 50)
    print()
    print("To test with a real image:")
    print("1. Load an image file")
    print("2. Convert to base64")
    print("3. Call the functions")
    print()
    print("Example:")
    print("""
    from devices.firebase_vision import analyze_mail
    import base64
    
    with open('test_image.jpg', 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    result = analyze_mail(image_data)
    print(result)
    # Expected output:
    # {
    #     "type": "package",
    #     "size": "medium",
    #     "carrier": "Amazon",
    #     "confidence": 0.92,
    #     "text": "extracted text...",
    #     "carriers": ["Amazon"]
    # }
    """)

if __name__ == "__main__":
    test_functions()







