import unittest
import logging
import numpy as np
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from unittest.mock import MagicMock
import sys
import os

# Mock sklearn BEFORE importing engine
sys.modules["sklearn"] = MagicMock()
sys.modules["sklearn.experimental"] = MagicMock()
sys.modules["sklearn.impute"] = MagicMock()
sys.modules["sklearn.linear_model"] = MagicMock()

# Setup mock for IterativeImputer
mock_imputer = MagicMock()
sys.modules["sklearn.impute"].IterativeImputer = MagicMock(return_value=mock_imputer)

# Define transform behavior
def mock_transform_behavior(X):
    # Just fill NaNs with a dummy value (e.g. 100 for units, 2025 for year)
    # X columns: lat, lon, type, dev, units, year
    import numpy as np
    X_out = X.copy()
    # If units (index 4) is NaN, fill 123
    for i in range(len(X_out)):
        if np.isnan(X_out[i][4]): 
            X_out[i][4] = 123.0
        if np.isnan(X_out[i][5]):
             X_out[i][5] = 2025.0
    return X_out

mock_imputer.transform.side_effect = mock_transform_behavior

# Import models
from cg_rera_extractor.db.base import Base
from cg_rera_extractor.db.models import Project, ProjectImputation, Building
from ai.imputation.engine import ImputationEngine

# Configure logging to see engine output
logging.basicConfig(level=logging.INFO)

class TestImputationIntegration(unittest.TestCase):
    
    def setUp(self):
        # Setup in-memory SQLite for speed/isolation
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        # Seed Data
        self._seed_data()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def _seed_data(self):
        # 1. Create Complete Projects (Training Data)
        # Using lat/lon/type/developer as features
        
        # Project A (Small, 2024)
        p1 = Project(
            state_code="MH", rera_registration_number="P1", project_name="Alpha",
            latitude=18.52, longitude=73.85, # Pune
            proposed_end_date=date(2024, 12, 31)
        )
        b1 = Building(project=p1, building_name="A", total_units=50) # Total 50
        self.session.add_all([p1, b1])
        
        # Project B (Medium, 2025)
        p2 = Project(
            state_code="MH", rera_registration_number="P2", project_name="Beta",
            latitude=18.53, longitude=73.86, # Pune
            proposed_end_date=date(2025, 6, 30)
        )
        b2 = Building(project=p2, building_name="B", total_units=100)
        self.session.add_all([p2, b2])

        # Project C (Large, 2026)
        p3 = Project(
            state_code="MH", rera_registration_number="P3", project_name="Gamma",
            latitude=18.54, longitude=73.87, # Pune
            proposed_end_date=date(2026, 12, 31)
        )
        b3 = Building(project=p3, building_name="C", total_units=200)
        self.session.add_all([p3, b3])
        
        self.session.commit()
        
        # 2. Create Incomplete Project (Target)
        # Similar location to P2/beta (should predict ~2025, ~100 units)
        self.p_inc = Project(
            state_code="MH", rera_registration_number="P_INC", project_name="Unknown",
            latitude=18.53, longitude=73.86,
            proposed_end_date=None # MISSING
        )
        # No building units info
        self.session.add(self.p_inc)
        self.session.commit()

    def test_imputation_flow(self):
        """
        Verify that ImputationEngine:
        1. Trains on seeded data.
        2. Predicts missing values for p_inc.
        3. Saves to DB.
        """
        engine = ImputationEngine(self.session)
        
        # 1. Train
        engine.train()
        self.assertTrue(engine.is_trained)
        
        # 2. Predict
        prediction = engine.predict_project(self.p_inc.id)
        print(f"DEBUG: Prediction result: {prediction}")
        
        # Check we got predicted fields
        self.assertIn("proposed_end_date", prediction)
        self.assertIn("total_units", prediction)
        
        # Check logic (Mocked behavior)
        # Expectation: Units = 123, Year = 2025
        pred_units = prediction["total_units"]
        self.assertEqual(pred_units, 123)
        
        # 3. Save
        engine.save_imputation(self.p_inc.id, prediction)
        
        # 4. Verify DB
        imp_record = self.session.query(ProjectImputation).filter_by(project_id=self.p_inc.id).first()
        self.assertIsNotNone(imp_record)
        self.assertEqual(imp_record.model_name, "IterativeImputer_v1")
        self.assertEqual(imp_record.imputed_data['total_units'], 123)
        self.assertEqual(imp_record.imputed_data['proposed_end_date'], "2025-12-31")

if __name__ == "__main__":
    unittest.main()
