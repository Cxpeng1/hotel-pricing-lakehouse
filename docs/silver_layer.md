# Silver Layer

The Silver layer contains cleaned and validated hotel booking data.

## Input

- `data/bronze/hotel_bookings_bronze.csv`

## Output

- `data/silver/hotel_bookings_silver.csv`

## Cleaning Applied

- Removed duplicate rows
- Filled missing `children` values with 0
- Filled missing `country` values with `Unknown`
- Filled missing `agent` and `company` values with 0
- Created `arrival_date`
- Created `total_nights`
- Created `total_guests`
- Created `booking_status`
- Created `estimated_revenue`
- Removed invalid rows where total guests, total nights, ADR, or arrival date were invalid

## Purpose

The Silver layer prepares reliable and clean data for Gold fact and dimension tables.