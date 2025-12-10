# 09 Price Trends Prompt

## Role
Data Scientist (Time Series).

## Goal
Implement **Price Trends & Demand Prediction**. Forecast future prices based on history.

## Inputs
- **Data:** `historical_prices` (TimeSeries: Date, Price, Locality).
- **Model:** `Prophet` or `ARIMA`.

## Outputs
- **Code:** `cg_rera_extractor/ai/analytics/forecasting.py`
- **Database:** `price_forecasts` table.

## Constraints
- **Horizon:** Predict next 6 months.
- **Confidence:** Must output upper/lower bounds.

## Files to Modify
- `cg_rera_extractor/ai/analytics/forecasting.py`

## Tests to Run
- `pytest tests/unit/ai/test_forecast.py`

## Acceptance Criteria
- [ ] Model fits historical data.
- [ ] Forecast dataframe generated.
- [ ] Results stored in DB.

### Example Test
```bash
python scripts/run_forecast.py --locality "Whitefield"
```
