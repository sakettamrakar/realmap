"""
Test RERA PDF extraction functionality.
"""
import pytest
import os
from unittest.mock import MagicMock, patch
from ai.rera.parser import ReraPdfParser

@pytest.fixture
def mock_db_session():
    return MagicMock()

def test_parser_initialization():
    parser = ReraPdfParser(use_ocr=False)
    assert parser.use_ocr is False

def test_llm_parsing_mock():
    parser = ReraPdfParser(use_ocr=False)
    dummy_text = "Proposed Completion Date: 31/12/2025\nLitigation Count: 0\nArchitect: John Doe"
    result = parser.parse_with_llm(dummy_text)
    
    assert "proposed_completion_date" in result
    assert "litigation_count" in result
    assert result["litigation_count"] == 0

@patch("ai.rera.parser.convert_from_path")
@patch("ai.rera.parser.pytesseract") 
def test_ocr_extraction_flow(mock_tess, mock_convert):
    # Setup mocks
    mock_convert.return_value = ["dummy_image"] # Return list of dummy images
    mock_tess.image_to_string.return_value = "Extracted Text Content"
    
    parser = ReraPdfParser(use_ocr=True)
    text = parser.extract_text("dummy.pdf")
    
    assert "Extracted Text Content" in text
    assert "--- Page 1 ---" in text

def test_process_file_flow(mock_db_session):
    with patch("ai.rera.parser.ReraPdfParser.extract_text") as mock_extract:
        mock_extract.return_value = "Mock PDF Content"
        
        parser = ReraPdfParser(use_ocr=False)
        
        # We need to mock os.path.exists to True so process_file doesn't raise error
        with patch("os.path.exists", return_value=True):
             # We also need to mock the ReraFiling model import/creation inside process_file
             # This is tricky because it imports inside the method.
             # An easier integration test is better, but here we can check if it calls db.add
             
             with patch("cg_rera_extractor.db.models.ReraFiling") as MockModel:
                instance = MockModel.return_value
                instance.id = 1
                
                result = parser.process_file("dummy.pdf", project_id=123, db=mock_db_session)
                
                mock_db_session.add.assert_called()
                mock_db_session.commit.assert_called()
                assert result["filing_id"] == 1
