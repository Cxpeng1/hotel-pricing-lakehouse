
DROP TABLE IF EXISTS fact_booking_predictions;

CREATE TABLE fact_booking_predictions (
    prediction_id INT PRIMARY KEY,
    fact_booking_id INT,
    cancellation_probability NUMERIC(10,6),
    predicted_cancelled INT,
    risk_level VARCHAR(50),
    booking_value NUMERIC(12,2),
    expected_revenue_at_risk NUMERIC(12,2),
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    prediction_timestamp TIMESTAMP
);

\copy fact_booking_predictions FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/ml/fact_booking_predictions.csv' WITH (FORMAT csv, HEADER true);

select * from fact_booking_predictions limit 10;