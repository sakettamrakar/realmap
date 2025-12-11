import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

from cg_rera_extractor.db.models import Project, ProjectImputation

logger = logging.getLogger("ai.imputation.engine")

class ImputationEngine:
    """
    AI-powered engine to impute missing data for Real Estate Projects.
    Uses sklearn's IterativeImputer (MICE) with BayesianRidge.
    
    Target Features:
    - total_units
    - proposed_end_date (via 'possession_year' transformation)
    """

    def __init__(self, session: Session):
        self.session = session
        self.model = None
        self.is_trained = False
        self.trained_features = None  # Track which features were actually used in training
        
        # Features used for prediction
        self.feature_cols = [
            'latitude', 
            'longitude', 
            'project_type_encoded', 
            'developer_id'
        ]
        
        # Target columns we want to fill
        self.target_cols = ['total_units_impute', 'possession_year_impute']
        
        self.all_cols = self.feature_cols + self.target_cols

    def load_training_data(self) -> pd.DataFrame:
        """
        Fetch projects features from DB.
        
        We construct a DataFrame where:
        - total_units_impute = project.total_units (Nan if missing)
        - possession_year_impute = project.proposed_end_date.year (NaN if missing)
        """
        logger.info("Loading training data from DB...")
        stmt = select(Project)
        projects = self.session.scalars(stmt).all()
        
        data = []
        for p in projects:
            # Safe access to buildings and promoters
            try:
                total_units = None
                if p.buildings and len(p.buildings) > 0 and p.buildings[0].total_units:
                    total_units = float(p.buildings[0].total_units)
                elif p.unit_types and len(p.unit_types) > 0 and p.unit_types[0].total_units:
                    total_units = float(p.unit_types[0].total_units)
                    
                developer_id = float(p.promoters[0].id) if p.promoters and len(p.promoters) > 0 else 0.0
                
                row = {
                    'id': p.id,
                    'latitude': float(p.latitude) if p.latitude else np.nan,
                    'longitude': float(p.longitude) if p.longitude else np.nan,
                    'developer_id': developer_id,
                    # Simple encoding: Residential=1, Commercial=2, etc. (Placeholder)
                    'project_type_encoded': 1.0, 
                    
                    # Targets
                    'total_units_impute': total_units if total_units is not None else np.nan,
                    'possession_year_impute': float(p.proposed_end_date.year) if p.proposed_end_date else np.nan
                }
            except (IndexError, AttributeError) as e:
                logger.warning(f"Error accessing data for project {p.id}: {e}")
                continue
            # Fallback for total_units if possible
            if pd.isna(row['total_units_impute']):
                 # Try to sum buildings? For now just keep NaN
                 pass
                 
            data.append(row)
            
        df = pd.DataFrame(data)
        logger.info(f"Loaded {len(df)} rows. Feature columns: {self.all_cols}")
        return df

    def train(self):
        """
        Train the IterativeImputer on the dataset.
        """
        df = self.load_training_data()
        
        if df.empty:
            logger.warning("No data to train on.")
            return

        # Prepare X matrix
        # We drop ID for training
        X = df[self.all_cols].values
        
        logger.info("Training IterativeImputer (BayesianRidge)...")
        self.model = IterativeImputer(
            estimator=BayesianRidge(),
            max_iter=10,
            random_state=42
        )
        self.model.fit(X)
        self.is_trained = True
        
        # Store which features have any non-NaN values
        # This helps us map predictions back correctly
        self.trained_features = []
        for i, col in enumerate(self.all_cols):
            if not df[col].isna().all():
                self.trained_features.append(col)
        
        logger.info(f"Model trained successfully. Active features: {self.trained_features}")
        logger.info("Model trained successfully.")

    def predict_project(self, project_id: int) -> Dict[str, Any]:
        """
        Predict missing values for a specific project.
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call train() first.")
            
        # Re-fetch specific project to ensure fresh state
        p = self.session.get(Project, project_id)
        if not p:
            return {}
            
        # Construct feature vector consistent with training
        # Safe access to buildings and promoters
        try:
            total_units = None
            if p.buildings and len(p.buildings) > 0 and p.buildings[0].total_units:
                total_units = float(p.buildings[0].total_units)
                
            developer_id = float(p.promoters[0].id) if p.promoters and len(p.promoters) > 0 else 0.0
            
            row = {
                'latitude': float(p.latitude) if p.latitude else np.nan,
                'longitude': float(p.longitude) if p.longitude else np.nan,
                'project_type_encoded': 1.0, 
                'developer_id': developer_id,
                
                # Original values (could be NaN)
                'total_units_impute': total_units if total_units is not None else np.nan,
                'possession_year_impute': float(p.proposed_end_date.year) if p.proposed_end_date else np.nan
            }
        except (IndexError, AttributeError) as e:
            logger.error(f"Error accessing data for project {project_id}: {e}")
            return {}
        
        # Create 1-row DataFrame
        df_single = pd.DataFrame([row], columns=self.all_cols) # Ensure column order
        X_in = df_single.values
        
        # Predict
        X_out = self.model.transform(X_in)
        
        # Map predictions back to dict
        # X_out contains only the features that were trained (non-all-NaN columns)
        # So we need to map using trained_features, not all_cols
        logger.debug(f"X_in shape: {X_in.shape}, X_out shape: {X_out.shape}")
        logger.debug(f"Trained features: {self.trained_features}")
        
        result_dict = {}
        if X_out.shape[1] == len(self.trained_features):
            # Map output columns to trained feature names
            for i, col in enumerate(self.trained_features):
                result_dict[col] = X_out[0][i]
        else:
            # Fallback: assume same order as all_cols
            logger.warning(f"Output shape {X_out.shape[1]} doesn't match trained features count {len(self.trained_features)}")
            for i, col in enumerate(self.all_cols):
                if i < X_out.shape[1]:
                    result_dict[col] = X_out[0][i]
                else:
                    result_dict[col] = np.nan
                
        predicted_units = result_dict.get('total_units_impute', np.nan)
        predicted_year = result_dict.get('possession_year_impute', np.nan)
        
        logger.debug(f"Predicted units: {predicted_units}, year: {predicted_year}")
        
        # Only return what was originally missing AND was successfully predicted
        result = {}
        if pd.isna(row['total_units_impute']) and not pd.isna(predicted_units):
            result['total_units'] = int(max(0, round(predicted_units)))
        
        if pd.isna(row['possession_year_impute']) and not pd.isna(predicted_year):
             # Convert year to date approx
             year = int(round(predicted_year))
             result['proposed_end_date'] = f"{year}-12-31" # Approx end of year
             
        return result

    def save_imputation(self, project_id: int, data: Dict[str, Any]):
        """
        Save prediction to DB.
        """
        if not data:
            return

        imputation = ProjectImputation(
            project_id=project_id,
            imputed_data=data,
            confidence_score=0.85, # Placeholder for sklearn imputer confidence
            model_name="IterativeImputer_v1"
        )
        self.session.add(imputation)
        self.session.commit()
