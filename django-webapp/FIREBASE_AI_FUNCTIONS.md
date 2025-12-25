# Firebase AI Analysis Functions - Reference

Complete reference for Firebase AI analysis functions for mailbox detection.

## Function Overview

All functions accept a base64-encoded image string and return structured data.

## 1. `detect_mail_type(image) -> str`

Detects the type of mail item in the image.

**Parameters:**
- `image` (str): Base64 encoded image string

**Returns:**
- `"package"` - Package/box detected
- `"letter"` - Letter/paper detected  
- `"envelope"` - Envelope detected
- `"unknown"` - Unable to determine

**Example:**
```python
from devices.firebase_vision import detect_mail_type

mail_type = detect_mail_type(base64_image)
# Returns: "package"
```

**Implementation:**
- Uses Google Cloud Vision Object Localization
- Analyzes detected objects for mail-related keywords
- Returns type with highest confidence (> 0.3 threshold)

## 2. `read_text(image) -> str`

Extracts visible text from image using OCR.

**Parameters:**
- `image` (str): Base64 encoded image string

**Returns:**
- Extracted text as string (all detected text)

**Example:**
```python
from devices.firebase_vision import read_text

text = read_text(base64_image)
# Returns: "123 Main St\nNew York, NY 10001\nAmazon Prime"
```

**Implementation:**
- Uses Google Cloud Vision Text Detection
- Returns full text from first annotation
- Includes addresses, labels, tracking numbers, etc.

## 3. `detect_logos(image) -> list`

Detects shipping carrier logos and brand names.

**Parameters:**
- `image` (str): Base64 encoded image string

**Returns:**
- List of detected carrier names: `["Amazon", "FedEx", "UPS"]`

**Supported Carriers:**
- Amazon
- FedEx
- UPS
- USPS
- DHL
- OnTrac
- Lasership

**Example:**
```python
from devices.firebase_vision import detect_logos

carriers = detect_logos(base64_image)
# Returns: ["Amazon", "FedEx"]
```

**Implementation:**
- Uses Google Cloud Vision Logo Detection
- Also checks OCR text for carrier names
- Returns unique list of detected carriers

## 4. `estimate_size(image) -> str`

Estimates the size of the mail item.

**Parameters:**
- `image` (str): Base64 encoded image string

**Returns:**
- `"small"` - Small item (< 15% of image area)
- `"medium"` - Medium item (15-40% of image area)
- `"large"` - Large item (> 40% of image area)
- `"unknown"` - Unable to determine

**Example:**
```python
from devices.firebase_vision import estimate_size

size = estimate_size(base64_image)
# Returns: "medium"
```

**Implementation:**
- Uses Object Localization to get bounding boxes
- Calculates area coverage of detected objects
- Classifies based on percentage of image covered

## 5. `analyze_mail(image) -> dict`

Complete mail analysis with structured output.

**Parameters:**
- `image` (str): Base64 encoded image string

**Returns:**
```python
{
    "type": "package",           # "package", "letter", or "envelope"
    "size": "medium",            # "small", "medium", or "large"
    "carrier": "Amazon",         # Primary carrier or None
    "confidence": 0.92,          # 0.0 to 1.0 (float)
    "text": "extracted text...", # Full OCR text (string)
    "carriers": ["Amazon"]       # All detected carriers (list)
}
```

**Example:**
```python
from devices.firebase_vision import analyze_mail

result = analyze_mail(base64_image)
print(result)
# Output:
# {
#     "type": "package",
#     "size": "medium",
#     "carrier": "Amazon",
#     "confidence": 0.92,
#     "text": "123 Main St\nAmazon Prime\nTracking: 1Z999AA10123456784",
#     "carriers": ["Amazon"]
# }
```

**Usage:**
```python
# Access individual fields
mail_type = result['type']        # "package"
size = result['size']             # "medium"
carrier = result['carrier']       # "Amazon"
confidence = result['confidence'] # 0.92
text = result['text']             # Full text
all_carriers = result['carriers'] # ["Amazon"]
```

## Complete Example

```python
from devices.firebase_vision import analyze_mail
import base64

# Load image
with open('mailbox_photo.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Analyze
result = analyze_mail(image_data)

# Process results
if result['type'] == 'package':
    print(f"📦 Package detected!")
    print(f"Size: {result['size']}")
    print(f"Carrier: {result['carrier']}")
    print(f"Confidence: {result['confidence']*100:.1f}%")
    
    if 'Amazon' in result['carriers']:
        print("Amazon delivery detected!")
    
    if result['text']:
        print(f"Detected text: {result['text'][:100]}...")
```

## Integration with Django

The functions are automatically called when a capture is uploaded:

```python
# In devices/api_views.py
analysis_data = vision_service.analyze_mail(capture.image_base64)

# Results are stored in CaptureAnalysis model
analysis = CaptureAnalysis.objects.create(
    capture=capture,
    summary=f"{analysis_data['size']} {analysis_data['type']} from {analysis_data['carrier']}",
    package_detected=(analysis_data['type'] == 'package'),
    letter_detected=(analysis_data['type'] == 'letter'),
    envelope_detected=(analysis_data['type'] == 'envelope'),
    detected_text=analysis_data['text'],
    estimated_size=analysis_data['size'],
    confidence_score=analysis_data['confidence']
)
```

## Error Handling

All functions return safe defaults on error:

- `detect_mail_type()` → `"unknown"`
- `read_text()` → `""` (empty string)
- `detect_logos()` → `[]` (empty list)
- `estimate_size()` → `"unknown"`
- `analyze_mail()` → Full dict with `"unknown"` values and `confidence: 0.0`

## Performance

- **Average processing time**: 1-3 seconds per image
- **Concurrent requests**: Supported (Vision API handles concurrency)
- **Caching**: Consider caching results for identical images

## Best Practices

1. **Image Quality**: Higher resolution = better accuracy
2. **Lighting**: Ensure good lighting for better OCR
3. **Focus**: Blurry images reduce confidence scores
4. **Error Handling**: Always check confidence scores
5. **Logging**: Monitor analysis results for accuracy

## Testing

Test individual functions:

```python
# In Django shell: python manage.py shell
from devices.firebase_vision import detect_mail_type, analyze_mail
import base64

# Load test image
with open('test.jpg', 'rb') as f:
    img = base64.b64encode(f.read()).decode()

# Test mail type
print(detect_mail_type(img))

# Test full analysis
result = analyze_mail(img)
print(result)
```

## Troubleshooting

**Low confidence scores:**
- Check image quality
- Verify camera focus
- Ensure good lighting

**No carriers detected:**
- Logo may not be visible
- Check OCR text for carrier names
- Verify image contains shipping labels

**Type detection fails:**
- Image may not contain clear mail item
- Try different camera angle
- Check object detection logs







