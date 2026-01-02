"""
Text Cleaner - Post-processing for OCR Output

Cleans and normalizes OCR-extracted text to improve
accuracy and prepare for structured extraction.
"""

import re
import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Common OCR errors and corrections
COMMON_OCR_CORRECTIONS = {
    # Number/letter confusion
    "0": {"O": 0.3, "o": 0.2},  # Context-dependent
    "1": {"l": 0.4, "I": 0.4, "|": 0.5},
    "5": {"S": 0.3, "s": 0.2},
    "8": {"B": 0.2},
    
    # Common word errors
    "Registratjon": "Registration",
    "Certiticate": "Certificate",
    "Certlficate": "Certificate",
    "Promotor": "Promoter",
    "Develeper": "Developer",
    "Distrlct": "District",
    "Ralpur": "Raipur",
    "Tehsll": "Tehsil",
    "Appllcation": "Application",
    "Proiect": "Project",
    "Valldity": "Validity",
    "Complction": "Completion",
    "Completlon": "Completion",
    "Sanctloned": "Sanctioned",
    "Bulldlng": "Building",
    "Resldential": "Residential",
    "Commerclal": "Commercial",
    
    # Hindi transliteration errors
    "Rs,": "Rs.",
    "Sq,Ft": "Sq.Ft",
    "Sq,ft": "Sq.ft",
}

# Patterns for specific field extraction helpers
RERA_NUMBER_PATTERN = re.compile(
    r'P[CG]{1,2}[GRERA]{4,5}\d{6,12}',
    re.IGNORECASE
)

DATE_PATTERNS = [
    re.compile(r'\d{2}[-/]\d{2}[-/]\d{4}'),  # DD-MM-YYYY or DD/MM/YYYY
    re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}'),  # YYYY-MM-DD
    re.compile(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', re.I),
]

AMOUNT_PATTERN = re.compile(
    r'(?:Rs\.?|₹|INR)\s*[\d,]+(?:\.\d{2})?',
    re.IGNORECASE
)


@dataclass
class CleaningResult:
    """Result of text cleaning operation"""
    original_text: str
    cleaned_text: str
    corrections_made: List[Dict[str, str]]
    extracted_entities: Dict[str, List[str]]
    word_count_before: int
    word_count_after: int


class TextCleaner:
    """
    Clean and normalize OCR-extracted text.
    
    Features:
    - Fix common OCR errors
    - Normalize whitespace and formatting
    - Extract key entities (RERA numbers, dates, amounts)
    - Handle Hindi/English mixed text
    - Remove noise and artifacts
    
    Usage:
        cleaner = TextCleaner()
        result = cleaner.clean(ocr_text)
        print(result.cleaned_text)
    """
    
    def __init__(
        self,
        fix_ocr_errors: bool = True,
        normalize_whitespace: bool = True,
        extract_entities: bool = True,
        preserve_structure: bool = True
    ):
        """
        Initialize text cleaner.
        
        Args:
            fix_ocr_errors: Apply common OCR error corrections
            normalize_whitespace: Normalize spaces and newlines
            extract_entities: Extract key entities while cleaning
            preserve_structure: Try to preserve document structure
        """
        self.fix_ocr_errors = fix_ocr_errors
        self.normalize_whitespace = normalize_whitespace
        self.extract_entities = extract_entities
        self.preserve_structure = preserve_structure
    
    def clean(self, text: str) -> CleaningResult:
        """
        Clean OCR text with full processing.
        
        Args:
            text: Raw OCR text
            
        Returns:
            CleaningResult with cleaned text and metadata
        """
        if not text:
            return CleaningResult(
                original_text="",
                cleaned_text="",
                corrections_made=[],
                extracted_entities={},
                word_count_before=0,
                word_count_after=0
            )
        
        original = text
        corrections = []
        
        # Step 1: Remove OCR artifacts
        text = self._remove_artifacts(text)
        
        # Step 2: Fix common OCR errors
        if self.fix_ocr_errors:
            text, new_corrections = self._fix_ocr_errors(text)
            corrections.extend(new_corrections)
        
        # Step 3: Normalize whitespace
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        # Step 4: Fix punctuation
        text = self._fix_punctuation(text)
        
        # Step 5: Extract entities
        entities = {}
        if self.extract_entities:
            entities = self._extract_entities(text)
        
        # Step 6: Final cleanup
        text = self._final_cleanup(text)
        
        return CleaningResult(
            original_text=original,
            cleaned_text=text,
            corrections_made=corrections,
            extracted_entities=entities,
            word_count_before=len(original.split()),
            word_count_after=len(text.split())
        )
    
    def clean_simple(self, text: str) -> str:
        """
        Quick cleaning without detailed results.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text string
        """
        return self.clean(text).cleaned_text
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove common OCR artifacts and noise"""
        # Remove isolated special characters
        text = re.sub(r'(?<!\S)[^\w\s,.\-/:;()₹$%@#&*]+(?!\S)', '', text)
        
        # Remove repeated punctuation
        text = re.sub(r'([.,;:!?])\1+', r'\1', text)
        
        # Remove very short lines that are likely noise
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Keep if line has meaningful content
            if len(stripped) > 2 or stripped.isalnum():
                cleaned_lines.append(line)
            elif not stripped:  # Keep empty lines for structure
                cleaned_lines.append('')
        
        return '\n'.join(cleaned_lines)
    
    def _fix_ocr_errors(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Fix common OCR recognition errors"""
        corrections = []
        
        # Apply word-level corrections
        for wrong, right in COMMON_OCR_CORRECTIONS.items():
            if isinstance(right, str) and wrong in text:
                text = text.replace(wrong, right)
                corrections.append({"from": wrong, "to": right})
        
        # Fix RERA number format issues
        # Pattern: PCGRERA followed by date and sequence
        def fix_rera_number(match):
            rera = match.group(0).upper()
            # Ensure consistent format
            return rera.replace('O', '0').replace('l', '1').replace('I', '1')
        
        text = RERA_NUMBER_PATTERN.sub(fix_rera_number, text)
        
        # Fix common number OCR issues in context
        # e.g., "Rs. 1O,OOO" -> "Rs. 10,000"
        def fix_amount(match):
            amount = match.group(0)
            return amount.replace('O', '0').replace('o', '0')
        
        text = AMOUNT_PATTERN.sub(fix_amount, text)
        
        return text, corrections
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving structure"""
        if self.preserve_structure:
            # Normalize multiple spaces to single space within lines
            lines = text.split('\n')
            normalized_lines = []
            
            for line in lines:
                # Replace multiple spaces with single space
                line = re.sub(r' {2,}', ' ', line)
                # But preserve indentation
                leading_space = len(line) - len(line.lstrip())
                if leading_space > 0:
                    line = '  ' + line.lstrip()  # Normalize to 2-space indent
                normalized_lines.append(line)
            
            # Remove excessive blank lines (more than 2)
            result = []
            blank_count = 0
            for line in normalized_lines:
                if not line.strip():
                    blank_count += 1
                    if blank_count <= 2:
                        result.append('')
                else:
                    blank_count = 0
                    result.append(line)
            
            return '\n'.join(result)
        else:
            # Simple normalization - collapse all whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def _fix_punctuation(self, text: str) -> str:
        """Fix common punctuation issues"""
        # Add space after punctuation if missing
        text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
        
        # Fix space before punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Fix colon spacing in labels
        text = re.sub(r':\s*(?=\S)', ': ', text)
        
        # Fix parentheses spacing
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        
        return text
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract key entities from text"""
        entities = {
            "rera_numbers": [],
            "dates": [],
            "amounts": [],
            "phone_numbers": [],
            "emails": []
        }
        
        # RERA Numbers
        entities["rera_numbers"] = RERA_NUMBER_PATTERN.findall(text)
        
        # Dates
        for pattern in DATE_PATTERNS:
            entities["dates"].extend(pattern.findall(text))
        
        # Amounts
        entities["amounts"] = AMOUNT_PATTERN.findall(text)
        
        # Phone numbers (Indian format)
        phone_pattern = re.compile(r'(?:\+91[-\s]?)?[6-9]\d{9}')
        entities["phone_numbers"] = phone_pattern.findall(text)
        
        # Emails
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        entities["emails"] = email_pattern.findall(text)
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass"""
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove trailing whitespace from document
        text = '\n'.join(lines).strip()
        
        # Ensure single newline at end
        if text and not text.endswith('\n'):
            text += '\n'
        
        return text
    
    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """
        Extract key-value pairs from structured text.
        
        Looks for patterns like:
        - "Field Name: Value"
        - "Field Name : Value"
        - "Field Name - Value"
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            Dictionary of extracted key-value pairs
        """
        pairs = {}
        
        # Pattern for "Key: Value" or "Key : Value"
        pattern = re.compile(r'^([A-Za-z][A-Za-z\s]{2,30})\s*[:|-]\s*(.+)$', re.MULTILINE)
        
        for match in pattern.finditer(text):
            key = match.group(1).strip()
            value = match.group(2).strip()
            
            # Normalize key
            key = re.sub(r'\s+', '_', key.lower())
            
            if value and len(value) > 1:  # Skip empty or single-char values
                pairs[key] = value
        
        return pairs
    
    def segment_document(self, text: str) -> List[Dict[str, str]]:
        """
        Segment document into logical sections.
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            List of sections with title and content
        """
        sections = []
        
        # Common section headers
        section_patterns = [
            r'^(REGISTRATION\s+CERTIFICATE)',
            r'^(PROJECT\s+DETAILS?)',
            r'^(PROMOTER\s+DETAILS?)',
            r'^(LAND\s+DETAILS?)',
            r'^(BUILDING\s+DETAILS?)',
            r'^(BANK\s+DETAILS?)',
            r'^(VALIDITY)',
            r'^(TERMS?\s+AND\s+CONDITIONS?)',
        ]
        
        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        
        # Split by section headers
        parts = re.split(combined_pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        
        current_section = {"title": "HEADER", "content": ""}
        
        for part in parts:
            if part is None:
                continue
            part = part.strip()
            if not part:
                continue
            
            # Check if this is a section header
            is_header = False
            for pattern in section_patterns:
                if re.match(pattern, part, re.IGNORECASE):
                    # Save previous section
                    if current_section["content"].strip():
                        sections.append(current_section)
                    # Start new section
                    current_section = {"title": part.upper(), "content": ""}
                    is_header = True
                    break
            
            if not is_header:
                current_section["content"] += part + "\n"
        
        # Add final section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections


# Convenience function
def clean_text(text: str) -> str:
    """
    Quick function to clean OCR text.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text string
    """
    cleaner = TextCleaner()
    return cleaner.clean_simple(text)
