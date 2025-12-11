import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Mock PIL and numpy specifically for this test context if missing
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["numpy"] = MagicMock()

# Mock surya modules to ensure imports work in parser
sys.modules["surya"] = MagicMock()
sys.modules["surya.ocr"] = MagicMock()
sys.modules["surya.model"] = MagicMock()
sys.modules["surya.model.detection"] = MagicMock()
sys.modules["surya.model.recognition"] = MagicMock()
sys.modules["surya.model.recognition.model"] = MagicMock()
sys.modules["surya.model.recognition.processor"] = MagicMock()

from ai.ocr.parser import FloorPlanParser

class TestFloorPlanParser(unittest.TestCase):
    
    @patch("ai.ocr.parser.SURYA_AVAILABLE", True)
    @patch("ai.ocr.parser.run_ocr")
    @patch("ai.ocr.parser.load_model")
    @patch("ai.ocr.parser.load_processor")
    @patch("ai.ocr.parser.segformer")
    def test_parse_image_mocked_success(self, mock_segformer, mock_proc, mock_model, mock_run_ocr):
        """Test parsing logic when models are 'loaded' and run successfully."""
        
        # Setup mocks
        mock_segformer.load_processor.return_value = MagicMock()
        mock_segformer.load_model.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_proc.return_value = MagicMock()
        
        # Mock OCR output
        mock_prediction = MagicMock()
        # Mock text lines
        line1 = MagicMock()
        line1.text = "Master Bedroom"
        line1.bbox = [0,0,10,10]
        line1.confidence = 0.99
        
        line2 = MagicMock()
        line2.text = "12'x14'"
        line2.bbox = [20,20,30,30]
        line2.confidence = 0.95
        
        mock_prediction.text_lines = [line1, line2]
        mock_run_ocr.return_value = [mock_prediction]
        
        # Mock Image.open
        with patch("PIL.Image.open") as mock_img_open:
            mock_img_open.return_value = MagicMock()
            with patch("os.path.exists", return_value=True):
                
                parser = FloorPlanParser()
                result = parser.parse_image("/fake/path/image.jpg")
                
                self.assertTrue(result["parsed"])
                self.assertEqual(len(result["raw_text"]), 2)
                
                # Check room extraction heuristic
                rooms = result["rooms"]
                self.assertEqual(len(rooms), 2)
                labels = [r["label"] for r in rooms]
                self.assertIn("potential_room_name", labels)
                self.assertIn("potential_dim", labels)

    @patch("ai.ocr.parser.SURYA_AVAILABLE", False)
    def test_parse_no_deps(self):
        """Test behavior when deps are missing."""
        with patch("os.path.exists", return_value=True):
            parser = FloorPlanParser()
            result = parser.parse_image("/fake/path.jpg")
            self.assertFalse(result["parsed"])
            self.assertIn("OCR dependencies not available", result.get("error"))

if __name__ == "__main__":
    unittest.main()
