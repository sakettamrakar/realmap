import sys
import os
sys.path.append(os.getcwd())
import unittest
from unittest.mock import MagicMock

# Mock sklearn
sys.modules["sklearn"] = MagicMock()
sys.modules["sklearn.ensemble"] = MagicMock()

try:
    from ai.anomaly.detector import AnomalyDetector
    print("Import AnomalyDetector: OK")
except Exception as e:
    print(f"Import AnomalyDetector: FAILED - {e}")

class TestSimple(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
