-- Hotel Pricing Lakehouse Project - Load Gold Tables
-- Purpose: Load Gold CSV files into PostgreSQL using psql \copy

-- The load_gold_tables.psql file is used to load the Gold layer CSV files into PostgreSQL. Since I am running the loading process 
-- through the PostgreSQL terminal, I use \copy instead of COPY because \copy reads files from my local computer. The dimension tables
-- are loaded first because the fact table depends on them through foreign key relationships. After all dimension tables are loaded, 
-- the fact_bookings table is loaded last. This step turns the Gold CSV outputs from Python into proper PostgreSQL warehouse tables 
-- that can be queried using SQL and later connected to Power BI.



-- Clear existing data before reload
TRUNCATE TABLE 
    fact_bookings,
    dim_hotel,
    dim_date,
    dim_room_type,
    dim_country,
    dim_market_segment,
    dim_customer_segment,
    dim_meal
RESTART IDENTITY CASCADE;


-- Load dimension tables first

\copy dim_hotel(hotel_id, hotel) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_hotel.csv' WITH (FORMAT csv, HEADER true);

\copy dim_date(date_id, arrival_date, year, month, month_name, day, quarter, is_weekend) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_date.csv' WITH (FORMAT csv, HEADER true);

\copy dim_room_type(room_type_id, room_type_code, room_type_name) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_room_type.csv' WITH (FORMAT csv, HEADER true);

\copy dim_country(country_id, country) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_country.csv' WITH (FORMAT csv, HEADER true);

\copy dim_market_segment(market_segment_id, market_segment) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_market_segment.csv' WITH (FORMAT csv, HEADER true);

\copy dim_customer_segment(customer_segment_id, customer_type) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_customer_segment.csv' WITH (FORMAT csv, HEADER true);

\copy dim_meal(meal_id, meal, meal_plan) FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/dim_meal.csv' WITH (FORMAT csv, HEADER true);


-- Load fact table last


\copy fact_bookings(
    fact_booking_id,
    hotel_id,
    date_id,
    reserved_room_type_id,
    assigned_room_type_id,
    country_id,
    market_segment_id,
    customer_segment_id,
    meal_id,
    is_canceled,
    booking_status,
    lead_time,
    total_nights,
    total_guests,
    adr,
    booking_value,
    estimated_revenue,
    booking_changes,
    days_in_waiting_list,
    required_car_parking_spaces,
    total_of_special_requests
)
FROM 'C:/Users/cxpen/Documents/JOB/Portfolios/hotel-pricing-lakehouse/data/gold/fact_bookings.csv'
WITH (FORMAT csv, HEADER true);


-- Check row counts after loading

SELECT 'dim_hotel' AS table_name, COUNT(*) AS row_count FROM dim_hotel
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'dim_room_type', COUNT(*) FROM dim_room_type
UNION ALL
SELECT 'dim_country', COUNT(*) FROM dim_country
UNION ALL
SELECT 'dim_market_segment', COUNT(*) FROM dim_market_segment
UNION ALL
SELECT 'dim_customer_segment', COUNT(*) FROM dim_customer_segment
UNION ALL
SELECT 'dim_meal', COUNT(*) FROM dim_meal
UNION ALL
SELECT 'fact_bookings', COUNT(*) FROM fact_bookings;


--  test
SELECT 
    f.fact_booking_id,
    h.hotel,
    d.arrival_date,
    f.total_nights,
    f.total_guests,
    f.adr,
    f.estimated_revenue
FROM fact_bookings f
JOIN dim_hotel h
    ON f.hotel_id = h.hotel_id
JOIN dim_date d
    ON f.date_id = d.date_id
LIMIT 10;