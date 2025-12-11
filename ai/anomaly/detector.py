import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest

from cg_rera_extractor.db.models import Project, ProjectPricingSnapshot, DataQualityFlag, UnitType

logger = logging.getLogger("ai.anomaly.detector")

class AnomalyDetector:
    """
    detects price and area anomalies using Isolation Forest.
    Focuses on 'price_per_sqft' and 'carpet_area'.
    """

    def __init__(self, session: Session):
        self.session = session
        self.model = None
        self.is_trained = False
        self.contamination = 0.01 # Expect top 1% outliers
        
    def load_data(self) -> pd.DataFrame:
        """
        Load features for anomaly detection.
        We aggregate data at project level or unit level?
        Let's look at Price Per Sqft derived from pricing snapshots or unit types.
        """
        logger.info("Loading data for anomaly detection...")
        
        # Strategy: Get all unit types (most granular source of Area + Price)
        stmt = select(UnitType).where(
            UnitType.saleable_area_sqmt.is_not(None),
            UnitType.sale_price.is_not(None)
        )
        units = self.session.scalars(stmt).all()
        
        data = []
        for u in units:
            try:
                area = float(u.saleable_area_sqmt) if u.saleable_area_sqmt else np.nan
                price = float(u.sale_price) if u.sale_price else np.nan
                
                # Derive price_per_sqft (assuming sqmt input, converting to sqft not strictly needed for anomaly if consistent)
                # But let's work with raw numbers
                if area > 0 and price > 0:
                    pp_rate = price / area
                    
                    data.append({
                        'unit_id': u.id,
                        'project_id': u.project_id,
                        'area': area,
                        'price': price,
                        'price_per_unit_area': pp_rate
                    })
            except Exception:
                continue
                
        df = pd.DataFrame(data)
        logger.info(f"Loaded {len(df)} records for training.")
        return df

    def train(self, df: pd.DataFrame = None):
        """
        Train Isolation Forest.
        """
        if df is None:
            df = self.load_data()
            
        if df.empty:
            logger.warning("No data to train.")
            return

        # Features: Area, Price, Rate
        X = df[['area', 'price', 'price_per_unit_area']].values
        
        logger.info("Training Isolation Forest...")
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X)
        self.is_trained = True
        logger.info("Model trained.")

    def detect(self, df: pd.DataFrame = None) -> List[Dict[str, Any]]:
        """
        Run detection on the dataset.
        Returns list of anomalies.
        """
        if not self.is_trained:
            logger.error("Model not trained.")
            return []
            
        if df is None:
            df = self.load_data() # Usually we might want to detect on NEW data, but for batch we scan all.
            
        if df.empty:
            return []
            
        X = df[['area', 'price', 'price_per_unit_area']].values
        
        # Predict: -1 for outliers, 1 for inliers
        preds = self.model.predict(X)
        scores = self.model.decision_function(X) # lower is more anomalous
        
        anomalies = []
        df['anomaly'] = preds
        df['score'] = scores
        
        outliers = df[df['anomaly'] == -1]
        logger.info(f"Detected {len(outliers)} anomalies.")
        
        for _, row in outliers.iterrows():
            # Determine which column is likely the cause?
            # Global outlier, hard to say specific col without interpretation.
            # We flag the record generally.
            anomalies.append({
                'project_id': int(row['project_id']),
                'column_name': 'price_area_mix', # Generic label for multivariate
                'outlier_value': float(row['price_per_unit_area']),
                'anomaly_score': float(row['score'])
            })
            
        return anomalies

    def save_flags(self, anomalies: List[Dict[str, Any]]):
        """
        Save findings to DB.
        """
        if not anomalies:
            return
            
        count = 0
        for item in anomalies:
            # simple check to avoid dupes? (optional, for now just insert)
            flag = DataQualityFlag(
                project_id=item['project_id'],
                column_name=item['column_name'],
                outlier_value=item['outlier_value'],
                anomaly_score=item['anomaly_score'],
                is_reviewed=False
            )
            self.session.add(flag)
            count += 1
        
        self.session.commit()
        logger.info(f"Saved {count} data quality flags.")
