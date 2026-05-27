-- business analysis queries.

/*
1. Total Bookings by Hotel
*/
SELECT 
    h.hotel,
    COUNT(*) AS total_bookings
FROM fact_bookings f
JOIN dim_hotel h
    ON f.hotel_id = h.hotel_id
GROUP BY h.hotel
ORDER BY total_bookings DESC;

/*
2. Estimated revenue by hotel
*/
select h.hotel, sum(f.estimated_revenue) as total_estimated_revenue
from fact_bookings f join dim_hotel h
on f.hotel_id = h.hotel_id
group by h.hotel;


/*
3. Cancellation rate by hotel
*/
select * from fact_bookings;

select h.hotel, sum(f.is_canceled) as total_cancellations, count(*) as total_bookings, 
       round(100.0 * sum(f.is_canceled) / count(*), 2) as cancellation_rate
from fact_bookings f join dim_hotel h on f.hotel_id = h.hotel_id
group by h.hotel;

/*
4. Monthly revenue trend
*/
SELECT 
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.estimated_revenue), 2) AS total_estimated_revenue
FROM fact_bookings f
JOIN dim_date d
    ON f.date_id = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;
/*
5. Average ADR by room type
*/

SELECT 
    r.room_type_name,
    ROUND(AVG(f.adr), 2) AS average_adr,
    COUNT(*) AS total_bookings
FROM fact_bookings f
JOIN dim_room_type r
    ON f.reserved_room_type_id = r.room_type_id
GROUP BY r.room_type_name
ORDER BY average_adr DESC;

--------------------------------------------------------------------------------------------------------------------------------
-- Booking Demand Trend
-- 1. Which months have the highest booking volume?
select d.month_name, count(*) as total_bookings
from fact_bookings f join dim_date d
on f.date_id = d.date_id
group by d.month_name
order by total_bookings desc;

-- 2. Is demand higher in summer or weekends?

SELECT
    CASE 
        WHEN d.month IN (6, 7, 8) THEN 'Summer'
        ELSE 'Non-Summer'
    END AS season_group,

    CASE 
        WHEN d.is_weekend = TRUE THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,

    COUNT(*) AS total_bookings,

    SUM(CASE 
        WHEN f.is_canceled = 0 THEN 1 
        ELSE 0 
    END) AS confirmed_bookings,

    ROUND(AVG(f.adr), 2) AS average_adr,

    ROUND(SUM(f.estimated_revenue), 2) AS total_estimated_revenue

FROM fact_bookings f
JOIN dim_date d
    ON f.date_id = d.date_id

GROUP BY 
    season_group,
    day_type

ORDER BY 
    season_group,
    day_type;



-- 3. Is City Hotel demand different from Resort Hotel demand?
SELECT 
    h.hotel,

    COUNT(*) AS total_bookings,

    SUM(CASE 
        WHEN f.is_canceled = 0 THEN 1 
        ELSE 0 
    END) AS confirmed_bookings,

    SUM(CASE 
        WHEN f.is_canceled = 1 THEN 1 
        ELSE 0 
    END) AS canceled_bookings,

    ROUND(
        SUM(CASE WHEN f.is_canceled = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS cancellation_rate_percentage,

    ROUND(AVG(f.adr), 2) AS average_adr,

    ROUND(SUM(f.estimated_revenue), 2) AS total_estimated_revenue

FROM fact_bookings f
JOIN dim_hotel h
    ON f.hotel_id = h.hotel_id

GROUP BY h.hotel
ORDER BY total_bookings DESC;
-- 4. Which year had the highest bookings?
select d.year, count(*) as total_bookings
from fact_bookings f join dim_date d
on f.date_id = d.date_id
group by d.year
order by total_bookings desc;

-----------------------------------------------------------------------------------------------------------------------------
-- Cancellation & Revenue Performance
-- 2.1 Which hotel has higher cancellation risk?

SELECT 
    h.hotel,
    COUNT(*) AS total_bookings,
    SUM(f.is_canceled) AS canceled_bookings,
    COUNT(*) - SUM(f.is_canceled) AS confirmed_bookings,
    ROUND(SUM(f.is_canceled) * 100.0 / COUNT(*), 2) AS cancellation_rate_percentage,
    ROUND(SUM(f.estimated_revenue), 2) AS confirmed_estimated_revenue
FROM fact_bookings f
JOIN dim_hotel h
    ON f.hotel_id = h.hotel_id
GROUP BY h.hotel
ORDER BY cancellation_rate_percentage DESC;

-- 2.2 Does longer lead time increase cancellation risk?

WITH lead_time_grouped AS (
    SELECT
        CASE
            WHEN lead_time <= 7 THEN '0-7 days'
            WHEN lead_time <= 30 THEN '8-30 days'
            WHEN lead_time <= 90 THEN '31-90 days'
            WHEN lead_time <= 180 THEN '91-180 days'
            ELSE '180+ days'
        END AS lead_time_group,

        CASE
            WHEN lead_time <= 7 THEN 1
            WHEN lead_time <= 30 THEN 2
            WHEN lead_time <= 90 THEN 3
            WHEN lead_time <= 180 THEN 4
            ELSE 5
        END AS lead_time_sort,

        is_canceled
    FROM fact_bookings
)

SELECT
    lead_time_group,
    COUNT(*) AS total_bookings,
    SUM(is_canceled) AS canceled_bookings,
    COUNT(*) - SUM(is_canceled) AS confirmed_bookings,
    ROUND(SUM(is_canceled) * 100.0 / COUNT(*), 2) AS cancellation_rate_percentage
FROM lead_time_grouped
GROUP BY lead_time_group, lead_time_sort
ORDER BY lead_time_sort;






-----------------------------------------------------------------------------------------------------------------------------
-- Customer and Market Segment Analysis

-- 3.1 Which market segment brings the most bookings and revenue?

SELECT
    m.market_segment,
    COUNT(*) AS total_bookings,
    COUNT(*) - SUM(f.is_canceled) AS confirmed_bookings,
    ROUND(SUM(f.estimated_revenue), 2) AS confirmed_estimated_revenue,
    ROUND(AVG(f.adr), 2) AS average_adr
FROM fact_bookings f
JOIN dim_market_segment m
    ON f.market_segment_id = m.market_segment_id
GROUP BY m.market_segment
ORDER BY confirmed_estimated_revenue DESC;
-- 3.2 Which customer type has the highest cancellation rate?

SELECT
    c.customer_type,
    COUNT(*) AS total_bookings,
    SUM(f.is_canceled) AS canceled_bookings,
    ROUND(SUM(f.is_canceled) * 100.0 / COUNT(*), 2) AS cancellation_rate_percentage,
    ROUND(SUM(f.estimated_revenue), 2) AS confirmed_estimated_revenue
FROM fact_bookings f
JOIN dim_customer_segment c
    ON f.customer_segment_id = c.customer_segment_id
GROUP BY c.customer_type
ORDER BY cancellation_rate_percentage DESC;






-----------------------------------------------------------------------------------------------------------------------------
-- Room Type and Pricing Analysis
-- 4.1 Which reserved room type has the highest average ADR?

SELECT
    r.room_type_name AS reserved_room_type,
    COUNT(*) AS total_bookings,
    ROUND(AVG(f.adr), 2) AS average_adr,
    ROUND(SUM(f.estimated_revenue), 2) AS confirmed_estimated_revenue
FROM fact_bookings f
JOIN dim_room_type r
    ON f.reserved_room_type_id = r.room_type_id
GROUP BY r.room_type_name
ORDER BY average_adr DESC;

-- 4.2 How often are customers assigned a different room type?

SELECT
    CASE
        WHEN f.reserved_room_type_id = f.assigned_room_type_id THEN 'Same Room Type'
        ELSE 'Different Room Type'
    END AS room_assignment_status,

    COUNT(*) AS total_bookings,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_of_bookings

FROM fact_bookings f
GROUP BY room_assignment_status
ORDER BY total_bookings DESC;


-----------------------------------------------------------------------------------------------------------------------------























































































