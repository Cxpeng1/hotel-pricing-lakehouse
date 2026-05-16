# Gold Layer

The Gold layer contains business-ready fact and dimension tables created from the cleaned Silver dataset.

## Fact Table

### fact_bookings

The fact table stores one row per hotel booking record.

Primary key:

- fact_booking_id

Foreign keys:

- hotel_id
- date_id
- reserved_room_type_id
- assigned_room_type_id
- country_id
- market_segment_id
- customer_segment_id
- meal_id

Measures:

- lead_time
- total_nights
- total_guests
- adr
- booking_value
- estimated_revenue
- booking_changes
- days_in_waiting_list
- required_car_parking_spaces
- total_of_special_requests

## Dimension Tables

- dim_hotel
- dim_date
- dim_room_type
- dim_country
- dim_market_segment
- dim_customer_segment
- dim_meal

## Purpose

The Gold layer prepares the data for SQL analytics and Power BI reporting using a star schema model.