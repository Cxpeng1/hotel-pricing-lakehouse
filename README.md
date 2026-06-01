# Hotel-Pricing-Lakehouse

### End-to-end hotel booking analytics project using Python, PostgreSQL, and Power BI to analyze booking demand, cancellation risk, and revenue performance.

## 📌Project Overview

This project analyzes hotel booking data to identify booking demand patterns, cancellation risk, revenue performance, and predicted cancellation probability across hotel types, market segments, customer types, and time periods. The project follows a lakehouse-style architecture with Bronze, Silver, and Gold layers. Cleaned and modeled data is loaded into PostgreSQL, visualized in Power BI, and extended with a machine learning model to predict booking cancellation risk and expected revenue at risk.

## ❓Business Problem

Hotels often face uncertainty in booking demand, cancellations, and revenue performance. High cancellation rates can reduce expected revenue, while seasonal demand patterns affect staffing, pricing, and marketing decisions.

This project aims to answer the following business questions:

- When does hotel booking demand increase or decrease?
- Which hotel type receives more bookings?
- Which customer or market segments are more likely to cancel?
- How much potential revenue is lost due to cancellations?
- Which months and segments generate the highest revenue?

## 📂Dataset

The dataset used in this project is the Hotel Booking Demand dataset from Kaggle.

Source: This project uses the [Hotel Booking Demand Dataset by Jesse Mostipak](https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand) from Kaggle.

The dataset contains booking records for City Hotel and Resort Hotel, including information such as:

- Booking status
- Arrival date
- Lead time
- Length of stay
- Number of guests
- Market segment
- Customer type
- Room type
- Average Daily Rate
- Special requests

The raw dataset is not modified in the Bronze layer. Data cleaning and business transformations are applied in the Silver and Gold layers.

## 🏗️Project Architecture

![Project Architecture](powerbi/images/Pipeline-flow.png)

## Data Pipeline

### Bronze Layer

The Bronze layer stores the raw hotel booking dataset with minimal changes. Technical metadata columns are added for traceability:

- `ingestion_timestamp`
- `source_file_name`
- `batch_id`

No business cleaning is applied at this stage.

### Silver Layer

The Silver layer applies data cleaning and feature engineering. Key cleaning steps include:

- Handling missing values in `country`, `agent`, `company`, and `children`
- Removing invalid records such as zero guests and zero-night bookings
- Removing negative ADR values
- Creating useful business columns such as:
  - `total_nights`
  - `total_guests`
  - `booking_status`
  - `booking_value`
  - `estimated_revenue`

### Gold Layer

The Gold layer transforms the cleaned Silver data into a star schema for reporting and analysis. The Gold layer includes one fact table and multiple dimension tables.


## Data Model

The Gold layer uses a star schema design to support efficient reporting in Power BI.
![Star Schema](powerbi/images/StarSchema.png)

The fact table contains booking-level metrics such as total nights, total guests, ADR, booking value, estimated revenue, cancellation status, and booking changes.'

## Power BI Dashboard

### Page 1: Executive Overview

Provides a high-level summary of hotel booking performance.
![Overview](powerbi/images/Overview.png)

### Page 2: Booking Cancellation Risk Analysis

Identifies where cancellation risk is concentrated and estimates potential revenue loss.
![Cancellation](powerbi/images/Cancellation.png)

### Page 3: Revenue & ADR Analysis

Analyzes estimated revenue, booking value, ADR, and revenue loss across hotel types, months, and market segments.
![Revenue](powerbi/images/Revenue.png)

### Page 4: Cancellation Risk Analysis
Predicts the likelihood of hotel booking cancellations using a supervised machine learning model. This page presents model performance metrics and a confusion matrix to evaluate how effectively the model identifies bookings with high cancellation risk.
![Cancellation](powerbi/images/Prediction.png)
## Machine Learning Extension: Cancellation Risk Prediction

A supervised machine learning model was developed to predict whether a booking is likely to be cancelled.

The target variable is:

- `is_canceled`
  - `0` = Not Cancelled
  - `1` = Cancelled

Three models were compared:

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 74.36% | 52.53% | 76.65% | 62.34% | 0.8299 |
| Random Forest | 81.46% | 63.79% | 76.40% | 69.53% | 0.8864 |
| XGBoost | 81.99% | 71.90% | 57.39% | 63.83% | 0.8802 |

Random Forest was selected because it provided the best balance for the business objective. It maintained high recall while improving precision, F1-score, and ROC-AUC compared with the baseline Logistic Regression model.

The model output was saved as `fact_booking_predictions.csv` and visualized in Power BI to show:

- Cancellation probability
- Risk level
- Predicted cancelled bookings
- High-risk bookings
- Expected revenue at risk

## Key Business Insights

- City Hotel generated higher booking volume than Resort Hotel, but also showed higher cancellation risk.
- Booking demand and estimated revenue were strongest during mid-year months, especially around July and August.
- Cancelled bookings increased faster than confirmed bookings, indicating that cancellation control is an important business issue.
- The Random Forest model identified high-risk bookings and estimated expected revenue at risk, helping hotels prioritize follow-up actions.
- Online TA and long lead-time bookings showed stronger cancellation risk patterns, suggesting that hotels should monitor these segments more closely.

## Repository Structure

```text
hotel-pricing-lakehouse/
│
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_bronze_ingestion.ipynb
│   ├── 03_silver_cleaning.ipynb
│   └── 04_gold_modeling.ipynb
│
├── sql/
│   ├── create_gold_tables.sql
│   ├── load_gold_tables.sql
│   └── analysis_queries.sql
│
├── powerbi/
│   └── hotel_booking_dashboard.pbix
│   └── images/
│
├── docs/
│   ├── bronze_layer.md
│   ├── silver_layer.md
│   ├── gold_layer.md
│   └── data_dictionary.md
│
│
└── README.md
```

## Data Quality Decisions

| Issue                 | Action                     |
| --------------------- | -------------------------- |
| Missing country       | Filled with `Unknown`      |
| Missing children      | Filled with `0`            |
| Missing agent/company | Filled with `0`            |
| Negative ADR          | Removed                    |
| Zero guests           | Removed                    |
| Zero-night bookings   | Removed                    |
| Duplicates            | Checked during exploration |




## Author

Created by Xu Peng
