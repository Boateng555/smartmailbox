"""
Firebase AI (Google Cloud Vision API) for Mailbox Analysis
Provides structured analysis functions for mail detection.
"""
import base64
import logging
import time
from typing import Dict, Optional
from google.cloud import vision
from google.oauth2 import service_account
from django.conf import settings

logger = logging.getLogger(__name__)


class FirebaseVisionService:
    """Service for analyzing mailbox images using Google Cloud Vision API"""
    
    def __init__(self):
        """Initialize the Vision API client"""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Vision API client with credentials"""
        try:
            # Check if credentials file path is provided
            credentials_path = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            
            if credentials_path:
                # Use service account credentials from file
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-vision']
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.info("Firebase Vision client initialized with service account file")
            else:
                # Try to use default credentials (for GCP environments)
                try:
                    self.client = vision.ImageAnnotatorClient()
                    logger.info("Firebase Vision client initialized with default credentials")
                except Exception as e:
                    logger.error(f"Failed to initialize Vision client: {str(e)}")
                    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Vision API will not work.")
                    self.client = None
        except Exception as e:
            logger.error(f"Error initializing Firebase Vision client: {str(e)}")
            self.client = None
    
    def detect_mail_type(self, image: str) -> str:
        """
        Detect mail type from image.
        
        Args:
            image: Base64 encoded image string or vision.Image object
            
        Returns:
            "letter", "package", or "envelope"
        """
        if not self.client:
            logger.error("Vision API client not initialized")
            return "unknown"
        
        try:
            # Convert base64 to vision.Image if needed
            if isinstance(image, str):
                image_data = base64.b64decode(image)
                vision_image = vision.Image(content=image_data)
            else:
                vision_image = image
            
            # Use object localization to detect mail-related objects
            response = self.client.object_localization(image=vision_image)
            
            # Check detected objects for mail types
            package_score = 0.0
            letter_score = 0.0
            envelope_score = 0.0
            
            for obj in response.localized_object_annotations:
                label = obj.name.lower()
                confidence = obj.score
                
                # Check for package indicators
                if any(keyword in label for keyword in ['package', 'box', 'parcel', 'container', 'carton']):
                    package_score = max(package_score, confidence)
                
                # Check for letter indicators
                if any(keyword in label for keyword in ['letter', 'paper', 'document', 'mail']):
                    letter_score = max(letter_score, confidence)
                
                # Check for envelope indicators
                if any(keyword in label for keyword in ['envelope', 'mailer']):
                    envelope_score = max(envelope_score, confidence)
            
            # Return type with highest confidence
            if package_score > letter_score and package_score > envelope_score and package_score > 0.3:
                return "package"
            elif envelope_score > letter_score and envelope_score > 0.3:
                return "envelope"
            elif letter_score > 0.3:
                return "letter"
            else:
                # Default to package if no clear match
                return "package"
                
        except Exception as e:
            logger.error(f"Error detecting mail type: {str(e)}", exc_info=True)
            return "unknown"
    
    def read_text(self, image: str) -> str:
        """
        Extract visible text from image using OCR.
        
        Args:
            image: Base64 encoded image string or vision.Image object
            
        Returns:
            Extracted text as string
        """
        if not self.client:
            logger.error("Vision API client not initialized")
            return ""
        
        try:
            # Convert base64 to vision.Image if needed
            if isinstance(image, str):
                image_data = base64.b64decode(image)
                vision_image = vision.Image(content=image_data)
            else:
                vision_image = image
            
            # Perform text detection
            response = self.client.text_detection(image=vision_image)
            
            if response.text_annotations:
                # First annotation contains all detected text
                return response.text_annotations[0].description
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error reading text: {str(e)}", exc_info=True)
            return ""
    
    def detect_logos(self, image: str) -> list:
        """
        Detect shipping carrier logos (Amazon, FedEx, UPS, etc.).
        
        Args:
            image: Base64 encoded image string or vision.Image object
            
        Returns:
            List of detected carrier names (e.g., ["Amazon", "FedEx"])
        """
        if not self.client:
            logger.error("Vision API client not initialized")
            return []
        
        try:
            # Convert base64 to vision.Image if needed
            if isinstance(image, str):
                image_data = base64.b64decode(image)
                vision_image = vision.Image(content=image_data)
            else:
                vision_image = image
            
            # Detect logos
            response = self.client.logo_detection(image=vision_image)
            
            carriers = []
            known_carriers = ['Amazon', 'FedEx', 'UPS', 'USPS', 'DHL', 'OnTrac', 'Lasership']
            
            for logo in response.logo_annotations:
                logo_name = logo.description
                # Check if it's a known carrier
                for carrier in known_carriers:
                    if carrier.lower() in logo_name.lower():
                        if carrier not in carriers:
                            carriers.append(carrier)
            
            # Also check OCR text for carrier names
            text = self.read_text(vision_image).upper()
            for carrier in known_carriers:
                if carrier.upper() in text and carrier not in carriers:
                    carriers.append(carrier)
            
            return carriers
            
        except Exception as e:
            logger.error(f"Error detecting logos: {str(e)}", exc_info=True)
            return []
    
    def estimate_size(self, image: str) -> str:
        """
        Estimate the size of mail item (small, medium, large).
        
        Args:
            image: Base64 encoded image string or vision.Image object
            
        Returns:
            "small", "medium", or "large"
        """
        if not self.client:
            logger.error("Vision API client not initialized")
            return "unknown"
        
        try:
            # Convert base64 to vision.Image if needed
            if isinstance(image, str):
                image_data = base64.b64decode(image)
                vision_image = vision.Image(content=image_data)
            else:
                vision_image = image
            
            # Use object localization to get bounding boxes
            response = self.client.object_localization(image=vision_image)
            
            if not response.localized_object_annotations:
                return "unknown"
            
            # Calculate total area covered by detected objects
            total_area = 0.0
            max_confidence = 0.0
            
            for obj in response.localized_object_annotations:
                confidence = obj.score
                max_confidence = max(max_confidence, confidence)
                
                # Calculate bounding box area
                vertices = obj.bounding_poly.normalized_vertices
                if len(vertices) >= 4:
                    x_coords = [v.x for v in vertices]
                    y_coords = [v.y for v in vertices]
                    width = max(x_coords) - min(x_coords)
                    height = max(y_coords) - min(y_coords)
                    area = width * height
                    total_area = max(total_area, area)  # Use largest object
            
            # Estimate size based on area coverage
            # Normalized coordinates: 0.0 to 1.0
            if total_area > 0.4:  # > 40% of image
                return "large"
            elif total_area > 0.15:  # > 15% of image
                return "medium"
            elif total_area > 0.05:  # > 5% of image
                return "small"
            else:
                return "small"  # Default to small
                
        except Exception as e:
            logger.error(f"Error estimating size: {str(e)}", exc_info=True)
            return "unknown"
    
    def analyze_mail(self, base64_image: str) -> Dict:
        """
        Complete mail analysis returning structured data.
        
        Args:
            base64_image: Base64 encoded image string
            
        Returns:
            Dictionary with structure:
            {
                "type": "package" | "letter" | "envelope",
                "size": "small" | "medium" | "large",
                "carrier": "Amazon" | "FedEx" | "UPS" | None,
                "confidence": 0.0-1.0,
                "text": "extracted text",
                "carriers": ["Amazon", "FedEx"]  # All detected carriers
            }
        """
        if not self.client:
            logger.error("Vision API client not initialized")
            return {
                "type": "unknown",
                "size": "unknown",
                "carrier": None,
                "confidence": 0.0,
                "text": "",
                "carriers": []
            }
        
        start_time = time.time()
        
        try:
            # Decode image once
            image_data = base64.b64decode(base64_image)
            vision_image = vision.Image(content=image_data)
            
            # Run all analyses
            mail_type = self.detect_mail_type(vision_image)
            size = self.estimate_size(vision_image)
            carriers = self.detect_logos(vision_image)
            text = self.read_text(vision_image)
            
            # Get primary carrier (first detected or most common)
            carrier = carriers[0] if carriers else None
            
            # Calculate overall confidence
            # Use object detection confidence as base
            response = self.client.object_localization(image=vision_image)
            max_confidence = 0.0
            if response.localized_object_annotations:
                max_confidence = max(obj.score for obj in response.localized_object_annotations)
            
            # Adjust confidence based on detection quality
            confidence = max_confidence
            if mail_type == "unknown":
                confidence *= 0.5  # Lower confidence if type unclear
            
            processing_time = time.time() - start_time
            logger.info(f"Mail analysis completed in {processing_time:.2f}s: type={mail_type}, size={size}, carrier={carrier}")
            
            return {
                "type": mail_type,
                "size": size.lower(),  # Ensure lowercase
                "carrier": carrier,
                "confidence": round(confidence, 2),
                "text": text,
                "carriers": carriers
            }
            
        except Exception as e:
            logger.error(f"Error analyzing mail: {str(e)}", exc_info=True)
            return {
                "type": "unknown",
                "size": "unknown",
                "carrier": None,
                "confidence": 0.0,
                "text": "",
                "carriers": []
            }


# Singleton instance
_vision_service = None

def get_vision_service() -> FirebaseVisionService:
    """Get or create the singleton Vision service instance"""
    global _vision_service
    if _vision_service is None:
        _vision_service = FirebaseVisionService()
    return _vision_service


# Convenience functions for direct use
def detect_mail_type(image: str) -> str:
    """Detect mail type: letter, package, or envelope"""
    service = get_vision_service()
    return service.detect_mail_type(image)


def read_text(image: str) -> str:
    """Extract visible text from image"""
    service = get_vision_service()
    return service.read_text(image)


def detect_logos(image: str) -> list:
    """Detect shipping carrier logos"""
    service = get_vision_service()
    return service.detect_logos(image)


def estimate_size(image: str) -> str:
    """Estimate mail size: small, medium, or large"""
    service = get_vision_service()
    return service.estimate_size(image)


def analyze_mail(image: str) -> Dict:
    """Complete mail analysis with structured output"""
    service = get_vision_service()
    return service.analyze_mail(image)
