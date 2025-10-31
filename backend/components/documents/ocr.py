"""
OCR processing module with multi-language support.
"""

import asyncio
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import easyocr
import pytesseract
from langdetect import detect

from ..models import OCRResult, LanguageCode
from ..utils.settings import settings

logger = logging.getLogger(__name__)

class OCRProcessor:
    """OCR processing with multi-language support."""
    
    def __init__(self):
        self.easyocr_readers = {}
        self.confidence_threshold = settings.ocr_confidence_threshold
        
    def get_easyocr_reader(self, languages: List[str]):
        """Get or create EasyOCR reader for specified languages."""
        lang_key = ",".join(sorted(languages))
        
        if lang_key not in self.easyocr_readers:
            try:
                self.easyocr_readers[lang_key] = easyocr.Reader(languages)
                logger.info(f"Created EasyOCR reader for languages: {lang_key}")
            except Exception as e:
                logger.error(f"Failed to create EasyOCR reader: {e}")
                raise
                
        return self.easyocr_readers[lang_key]
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results."""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            if settings.image_enhancement:
                # Convert to grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Apply denoising
                denoised = cv2.fastNlMeansDenoising(gray)
                
                # Enhance contrast using CLAHE
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(denoised)
                
                # Apply Gaussian blur to reduce noise
                blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
                
                return blurred
            else:
                return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original image in grayscale as fallback
            img = cv2.imread(image_path)
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    def detect_language(self, text: str) -> Optional[LanguageCode]:
        """Detect language from extracted text."""
        try:
            if not text or not text.strip():
                return None
                
            detected = detect(text)
            
            # Map langdetect codes to our enum
            lang_mapping = {
                'th': LanguageCode.THAI,
                'en': LanguageCode.ENGLISH,
                'ja': LanguageCode.JAPANESE
            }
            
            return lang_mapping.get(detected)
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    async def extract_text_easyocr(self, image_path: str, languages: List[str]) -> Tuple[str, float, List]:
        """Extract text using EasyOCR."""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Get EasyOCR reader
            reader = self.get_easyocr_reader(languages)
            
            # Extract text
            results = reader.readtext(processed_img)
            
            if not results:
                return "", 0.0, []
            
            # Combine text and calculate average confidence
            texts = []
            confidences = []
            bbox_data = []
            
            for bbox, text, confidence in results:
                if confidence >= self.confidence_threshold:
                    texts.append(text.strip())
                    confidences.append(confidence)
                    bbox_data.append({
                        'bbox': bbox,
                        'text': text,
                        'confidence': confidence
                    })
            
            combined_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return combined_text, avg_confidence, bbox_data
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return "", 0.0, []
    
    async def extract_text_tesseract(self, image_path: str, language: str = "eng") -> Tuple[str, float]:
        """Extract text using Tesseract OCR as fallback."""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Tesseract language mapping
            tesseract_langs = {
                'th': 'tha',
                'en': 'eng', 
                'ja': 'jpn'
            }
            
            lang_code = tesseract_langs.get(language, 'eng')
            
            # Extract text with confidence
            text = pytesseract.image_to_string(
                processed_img,
                lang=lang_code,
                config='--psm 6'
            )
            
            # Get confidence data
            confidence_data = pytesseract.image_to_data(
                processed_img,
                lang=lang_code,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [
                int(conf) for conf in confidence_data['conf'] 
                if int(conf) > 0
            ]
            
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return "", 0.0
    
    async def process_image(self, image_path: str, languages: Optional[List[str]] = None) -> OCRResult:
        """Process image and extract text with OCR."""
        import time
        start_time = time.time()
        
        if languages is None:
            languages = settings.ocr_language_list
        
        try:
            # Try EasyOCR first
            text, confidence, bbox_data = await self.extract_text_easyocr(image_path, languages)
            
            # If EasyOCR fails or has low confidence, try Tesseract
            if confidence < self.confidence_threshold:
                logger.info(f"EasyOCR confidence too low ({confidence:.2f}), trying Tesseract")
                
                # Try primary language with Tesseract
                primary_lang = languages[0] if languages else 'en'
                tesseract_text, tesseract_conf = await self.extract_text_tesseract(image_path, primary_lang)
                
                if tesseract_conf > confidence:
                    text = tesseract_text
                    confidence = tesseract_conf
                    bbox_data = []  # Tesseract doesn't provide bbox in this implementation
            
            # Detect language from extracted text
            detected_lang = self.detect_language(text)
            if detected_lang is None:
                # Default to first specified language
                detected_lang = LanguageCode(languages[0]) if languages else LanguageCode.ENGLISH
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text,
                confidence=confidence,
                language=detected_lang,
                processing_time=processing_time,
                bbox_data=bbox_data
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {e}")
            processing_time = time.time() - start_time
            
            return OCRResult(
                text="",
                confidence=0.0,
                language=LanguageCode.ENGLISH,
                processing_time=processing_time,
                bbox_data=[]
            )

# Global OCR processor instance
ocr_processor = OCRProcessor()