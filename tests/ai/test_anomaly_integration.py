import unittest
import logging
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
import sys
import os
sys.path.append(os.getcwd())
import numpy as np

sys.modules["sklearn"] = MagicMock()
sys.modules["sklearn.ensemble"] = MagicMock()

mock_iso_forest = MagicMock()
sys.modules["sklearn.ensemble"].IsolationForest = MagicMock(return_value=mock_iso_forest)

def mock_predict(X):
    # X shape is (N, 3): [area, price, price_per_unit_area]
    # Logic: if price_per_unit_area (index 2) > 500, flag as -1 (anomaly), else 1 (normal)
    results = []
    for row in X:
        rate = row[2]
        if rate > 500 or rate < 10: # extreme
            results.append(-1)
        else:
            results.append(1)
    return np.array(results)

def mock_decision_function(X):
    results = []
    for row in X:
        rate = row[2]
        if rate > 500:
            results.append(-0.8) # Strong anomaly
        else:
            results.append(0.5) # Normal
    return np.array(results)

mock_iso_forest.fit.return_value = None
mock_iso_forest.predict.side_effect = mock_predict
mock_iso_forest.decision_function.side_effect = mock_decision_function
# --- MOCK SKLEARN setup end ---


from cg_rera_extractor.db.base import Base
from cg_rera_extractor.db.models import Project, UnitType, DataQualityFlag
from ai.anomaly.detector import AnomalyDetector

logging.basicConfig(level=logging.INFO)

class TestAnomalyIntegration(unittest.TestCase):
    
    def setUp(self):
        # Setup in-memory SQLite
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        self._seed_data()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def _seed_data(self):
        # 1. Project
        p = Project(
            state_code="MH", rera_registration_number="P_TEST", project_name="Test Project",
            latitude=18.52, longitude=73.85
        )
        self.session.add(p)
        self.session.flush()
        
        # 2. Normal Units (Rate ~50-80)
        # Area 1000, Price 50000 -> Rate 50
        u1 = UnitType(project_id=p.id, type_name="1BHK", saleable_area_sqmt=100.0, sale_price=5000.0)
        u2 = UnitType(project_id=p.id, type_name="2BHK", saleable_area_sqmt=150.0, sale_price=7500.0) # Rate 50
        
        # 3. Anomaly Unit (Rate 1000)
        # Area 100, Price 100000 -> Rate 1000
        u_bad = UnitType(project_id=p.id, type_name="Penthouse", saleable_area_sqmt=100.0, sale_price=100000.0)
        
        self.session.add_all([u1, u2, u_bad])
        self.session.commit()
        self.p_id = p.id

    def test_detection_flow(self):
        try:
            detector = AnomalyDetector(self.session)
            
            # 1. Load
            df = detector.load_data()
            print(f"DEBUG: DF loaded. Len: {len(df)}")
            self.assertEqual(len(df), 3)
            
            # 2. Train
            detector.train(df)
            self.assertTrue(detector.is_trained)
            
            # 3. Detect
            anomalies = detector.detect(df)
            print(f"DEBUG: Anomalies: {anomalies}")
            
            # Expect 1 anomaly (u_bad)
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0]['project_id'], self.p_id)
            self.assertEqual(anomalies[0]['outlier_value'], 1000.0)
            
            # 4. Save
            detector.save_flags(anomalies)
            
            # 5. Verify DB
            flag = self.session.query(DataQualityFlag).filter_by(project_id=self.p_id).first()
            self.assertIsNotNone(flag)
            self.assertEqual(flag.column_name, 'price_area_mix')
            self.assertEqual(float(flag.outlier_value), 1000.0)
            self.assertEqual(float(flag.anomaly_score), -0.8)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

if __name__ == "__main__":
    unittest.main()
