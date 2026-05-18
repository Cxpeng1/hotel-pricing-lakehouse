-- Hotel Pricing Lakehouse Project - Create Gold Tables
-- Purpose: Create dimension and fact tables for the Gold warehouse layer in PostgreSQL

DROP TABLE IF EXISTS fact_bookings;
DROP TABLE IF EXISTS dim_hotel;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_room_type;
DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_market_segment;
DROP TABLE IF EXISTS dim_customer_segment;
DROP TABLE IF EXISTS dim_meal;

CREATE TABLE dim_hotel (
    hotel_id INT PRIMARY KEY,
    hotel VARCHAR(100)
);

Create table dim_date (
    date_id INT PRIMARY KEY,
    arrival_date DATE,
    year INT,
    month INT,
    month_name VARCHAR(20),
    day INT,
    quarter INT,
    is_weekend BOOLEAN
);

Create table dim_room_type (
    room_type_id INT PRIMARY KEY,
    room_type_code VARCHAR(10),
    room_type_name VARCHAR(50)
);

Create table dim_country (
    country_id INT PRIMARY KEY,
    country VARCHAR(100)
);

Create table dim_market_segment (
    market_segment_id INT PRIMARY KEY,
    market_segment VARCHAR(100)
);

Create table dim_customer_segment (
    customer_segment_id INT PRIMARY KEY,
    customer_type VARCHAR(100)
);

Create table dim_meal (
    meal_id INT PRIMARY KEY,
    meal VARCHAR(50),
    meal_plan VARCHAR(50)
);

CREATE TABLE fact_bookings (
    fact_booking_id INT PRIMARY KEY,

    hotel_id INT NOT NULL,
    date_id INT NOT NULL,
    reserved_room_type_id INT,
    assigned_room_type_id INT,
    country_id INT,
    market_segment_id INT,
    customer_segment_id INT,
    meal_id INT,

    is_canceled INT,
    booking_status VARCHAR(50),
    lead_time INT,
    total_nights INT,
    total_guests INT,
    adr NUMERIC(10, 2),
    booking_value NUMERIC(12, 2),
    estimated_revenue NUMERIC(12, 2),
    room_type_changed BOOLEAN,
    booking_changes INT,
    days_in_waiting_list INT,
    required_car_parking_spaces INT,
    total_of_special_requests INT,  

    Constraint fk_fact_hotel FOREIGN KEY (hotel_id) REFERENCES dim_hotel(hotel_id),
    Constraint fk_fact_date FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    CONSTRAINT fk_fact_reserved_room_type
        FOREIGN KEY (reserved_room_type_id)
        REFERENCES dim_room_type(room_type_id),

    CONSTRAINT fk_fact_assigned_room_type
        FOREIGN KEY (assigned_room_type_id)
        REFERENCES dim_room_type(room_type_id),
    Constraint fk_fact_country FOREIGN KEY (country_id) References dim_country(country_id),
    Constraint fk_fact_market_segment FOREIGN KEY (market_segment_id) REFERENCES dim_market_segment(market_segment_id),
    Constraint fk_fact_customer_segment FOREIGN KEY (customer_segment_id) REFERENCES dim_customer_segment(customer_segment_id),
    Constraint fk_fact_meal FOREIGN KEY (meal_id) REFERENCES dim_meal(meal_id)
);









