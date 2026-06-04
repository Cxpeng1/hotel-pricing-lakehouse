# Data Exploration Findings

## Executive Summary

This analysis explores hotel booking demand, cancellation behavior, revenue performance, and machine learning cancellation prediction results from the Hotel Booking Demand dataset.

The project follows a lakehouse-style pipeline:

- Raw source data: `119,390` booking records
- Silver cleaned data: `86,638` booking records
- Gold fact table: `86,638` booking records
- Prediction output: `86,638` booking-level predictions

After cleaning, the cancellation rate is `27.69%`, with `23,986` cancelled bookings and `62,652` non-cancelled bookings. City Hotel has higher booking volume and higher cancellation risk than Resort Hotel. Online Travel Agent bookings are the largest segment and also the strongest source of cancellation risk. Demand and revenue peak during mid-year months, especially July and August.

The machine learning extension uses a Random Forest model to predict cancellation probability and expected revenue at risk. The selected Random Forest model achieved `81.46%` accuracy, `69.53%` F1 score, and `0.8864` ROC-AUC. The prediction output identifies `15,558` high-risk bookings and estimates total expected revenue at risk of `14.93M`.

## Dataset Overview

The original dataset contains booking records for City Hotel and Resort Hotel. It includes booking status, arrival date, lead time, stay length, guest counts, country, market segment, customer type, room type, ADR, special requests, and reservation status.

### Row Counts

| Layer | Rows |
|---|---:|
| Raw | 119,390 |
| Silver | 86,638 |
| Gold fact table | 86,638 |
| Prediction output | 86,638 |

The Silver layer contains `32,752` fewer rows than the Raw layer after cleaning and validation.

### Raw Hotel Distribution

| Hotel Type | Raw Bookings |
|---|---:|
| City Hotel | 79,330 |
| Resort Hotel | 40,060 |

City Hotel represents the majority of bookings in the raw dataset.

## Data Quality Findings

The raw dataset contains several data quality issues that were handled in the Silver layer.

### Missing Values

| Column | Missing Values |
|---|---:|
| `company` | 112,593 |
| `agent` | 16,340 |
| `country` | 488 |
| `children` | 4 |

### Cleaning Decisions

| Issue | Action |
|---|---|
| Missing `country` | Filled with `Unknown` |
| Missing `children` | Filled with `0` |
| Missing `agent` and `company` | Filled with `0` |
| Duplicate records | Removed |
| Zero-guest bookings | Removed |
| Zero-night bookings | Removed |
| Invalid ADR values | Removed |
| Date fields | Converted into a usable `arrival_date` |
| Business metrics | Created `total_nights`, `total_guests`, `booking_status`, and `estimated_revenue` |

These cleaning steps reduce noise in the dataset and prepare the data for reliable reporting, SQL analysis, and model training.

## Booking Status Findings

After Silver cleaning:

| Booking Status | Bookings |
|---|---:|
| Not Canceled | 62,652 |
| Canceled | 23,986 |

The cleaned cancellation rate is `27.69%`. The raw cancellation rate was `37.04%`, but after removing invalid and duplicate records, the cancellation profile becomes more reliable for analysis.

## Hotel Type Findings

| Hotel | Bookings | Cancellations | Cancellation Rate | Estimated Revenue | Average ADR |
|---|---:|---:|---:|---:|---:|
| City Hotel | 53,043 | 16,022 | 30.21% | 18.77M | 111.76 |
| Resort Hotel | 33,595 | 7,964 | 23.71% | 15.69M | 100.12 |

### Key Findings

- City Hotel has higher booking volume than Resort Hotel.
- City Hotel also has a higher cancellation rate, at `30.21%` compared with Resort Hotel at `23.71%`.
- City Hotel has a higher average ADR, which means cancellations in this segment can have a larger revenue impact.
- Resort Hotel has fewer bookings but still contributes meaningful estimated revenue because of stay patterns and booking value.

## Country Findings

Top source countries by booking volume:

| Country | Bookings |
|---|---:|
| PRT | 26,864 |
| GBR | 10,400 |
| FRA | 8,813 |
| ESP | 7,228 |
| DEU | 5,385 |
| ITA | 3,056 |
| IRL | 3,014 |
| BEL | 2,078 |
| BRA | 1,988 |
| NLD | 1,908 |

### Key Findings

- Portugal (`PRT`) is the largest source country by a wide margin.
- European countries dominate the top booking sources.
- Country-level segmentation is useful for market targeting, cancellation monitoring, and regional demand planning.

## Market Segment Findings

| Market Segment | Bookings | Cancellations | Cancellation Rate | Estimated Revenue |
|---|---:|---:|---:|---:|
| Online TA | 51,285 | 18,230 | 35.55% | 22.26M |
| Offline TA/TO | 13,749 | 2,056 | 14.95% | 5.42M |
| Direct | 11,652 | 1,733 | 14.87% | 4.86M |
| Groups | 4,891 | 1,331 | 27.21% | 1.24M |
| Corporate | 4,155 | 507 | 12.20% | 0.59M |
| Complementary | 682 | 83 | 12.17% | 0.01M |
| Aviation | 222 | 44 | 19.82% | 0.08M |
| Undefined | 2 | 2 | 100.00% | 0.00M |

### Key Findings

- Online TA is the largest booking channel and contributes the highest number of cancellations.
- Online TA has a cancellation rate of `35.55%`, much higher than Direct and Offline TA/TO bookings.
- Groups also show elevated cancellation risk at `27.21%`.
- Corporate bookings have relatively low cancellation risk at `12.20%`.
- The Undefined segment has a 100% cancellation rate, but only two records, so it should not be treated as a meaningful business segment.

## Customer Type Findings

| Customer Type | Bookings | Cancellations | Cancellation Rate | Estimated Revenue |
|---|---:|---:|---:|---:|
| Transient | 71,366 | 21,640 | 30.32% | 29.24M |
| Transient-Party | 11,617 | 1,781 | 15.33% | 3.43M |
| Contract | 3,119 | 512 | 16.42% | 1.64M |
| Group | 536 | 53 | 9.89% | 0.14M |

### Key Findings

- Transient customers dominate the dataset and account for most cancellations.
- Transient customers have a cancellation rate of `30.32%`, making them a major risk group.
- Group customers show the lowest cancellation rate, but they represent a much smaller share of total bookings.

## Monthly Demand and Revenue Findings

### Highest Booking Months

| Month | Bookings | Cancellations | Cancellation Rate | Estimated Revenue | Average ADR |
|---|---:|---:|---:|---:|---:|
| August | 11,194 | 3,622 | 32.36% | 7.24M | 151.70 |
| July | 9,988 | 3,195 | 31.99% | 5.86M | 136.46 |
| May | 8,296 | 2,440 | 29.41% | 3.12M | 111.95 |
| April | 7,870 | 2,403 | 30.53% | 2.79M | 104.10 |
| June | 7,721 | 2,351 | 30.45% | 3.50M | 120.41 |
| March | 7,439 | 1,827 | 24.56% | 2.05M | 82.41 |

### Highest Revenue Months

| Month | Estimated Revenue | Bookings | Average ADR |
|---|---:|---:|---:|
| August | 7.24M | 11,194 | 151.70 |
| July | 5.86M | 9,988 | 136.46 |
| June | 3.50M | 7,721 | 120.41 |
| May | 3.12M | 8,296 | 111.95 |
| April | 2.79M | 7,870 | 104.10 |
| September | 2.69M | 6,659 | 112.60 |

### Key Findings

- Demand peaks in August and July.
- August is the strongest month by both booking count and estimated revenue.
- ADR is also highest in August and July, showing stronger pricing power during peak season.
- The same high-demand months also have elevated cancellation rates, so revenue management should focus on both pricing and cancellation control during peak periods.

## Lead Time Findings

| Lead Time Bucket | Bookings | Cancellations | Cancellation Rate |
|---|---:|---:|---:|
| 0-7 days | 17,855 | 1,520 | 8.51% |
| 8-30 days | 16,234 | 4,139 | 25.50% |
| 31-90 days | 22,634 | 7,276 | 32.15% |
| 91-180 days | 18,190 | 6,379 | 35.07% |
| 181-365 days | 11,164 | 4,442 | 39.79% |
| 365+ days | 561 | 230 | 41.00% |

### Key Findings

- Cancellation risk increases as lead time increases.
- Bookings made within 7 days have the lowest cancellation rate at `8.51%`.
- Bookings made more than 180 days in advance have cancellation rates close to or above `40%`.
- Long lead-time bookings should be monitored closely because they are more likely to become unstable demand.

## Room Assignment Findings

| Room Type Changed | Bookings | Cancellation Rate |
|---|---:|---:|
| No | 73,978 | 31.60% |
| Yes | 12,660 | 4.80% |

### Key Findings

- Bookings where the assigned room differs from the reserved room show a much lower cancellation rate.
- This may happen because room assignment changes are only finalized closer to arrival or after the booking is more likely to be confirmed.
- This variable is useful for analysis, but should be handled carefully in predictive modeling because it may contain information that is only known later in the booking lifecycle.

## Special Request Findings

| Special Request Count | Bookings | Cancellation Rate |
|---|---:|---:|
| 0 | 43,432 | 33.50% |
| 1 | 28,804 | 22.54% |
| 2 | 11,739 | 21.42% |
| 3+ | 2,663 | 16.22% |

### Key Findings

- Bookings with no special requests have the highest cancellation rate.
- Cancellation risk decreases as the number of special requests increases.
- Guests who make special requests may have stronger booking intent.

## Deposit Type Findings

| Deposit Type | Bookings | Cancellations | Cancellation Rate |
|---|---:|---:|---:|
| No Deposit | 85,493 | 22,977 | 26.88% |
| Non Refund | 1,038 | 983 | 94.70% |
| Refundable | 107 | 26 | 24.30% |

### Key Findings

- Most bookings are No Deposit bookings.
- Non Refund bookings show a very high cancellation rate of `94.70%`.
- This pattern may reflect business rules, booking channel behavior, or historical cancellation labeling and should be investigated before using deposit type for operational decisions.

## Revenue Findings

| Metric | Value |
|---|---:|
| Total booking value | 34.45M |
| Gold estimated revenue | 22.97M |
| Average ADR | 107.25 |
| Average total nights | 3.65 |
| Average total guests | 2.03 |

### Key Findings

- Total booking value represents the potential value of all bookings.
- Gold estimated revenue is lower because cancelled bookings reduce realized or expected revenue.
- Revenue concentration is strongest in peak months, especially July and August.
- Online TA produces high revenue volume but also high cancellation exposure.

## Machine Learning Model Findings

### Objective

The prediction model estimates whether a booking is likely to be cancelled.

Target variable:

- `is_canceled`
  - `0` = Not cancelled
  - `1` = Cancelled

The model output is used to estimate cancellation probability, classify risk level, and calculate expected revenue at risk.

### Modeling Features

The model uses booking, customer, channel, and stay-related features, including:

- Hotel type
- Lead time
- Arrival month
- Weekend and weekday nights
- Number of adults, children, and babies
- Meal type
- Country
- Market segment
- Distribution channel
- Repeated guest flag
- Previous cancellations
- Previous non-cancelled bookings
- Reserved room type
- Deposit type
- Customer type
- ADR
- Car parking spaces
- Special requests
- Total nights
- Total guests

Categorical variables were handled with one-hot encoding, and numerical variables were imputed and scaled through a preprocessing pipeline.

### Model Comparison

Three models were trained and compared.

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 74.36% | 52.53% | 76.65% | 62.34% | 0.8299 |
| Random Forest | 81.46% | 63.79% | 76.40% | 69.53% | 0.8864 |
| XGBoost | 81.99% | 71.90% | 57.39% | 63.83% | 0.8802 |

### Model Selection

Random Forest was selected as the final model.

Although XGBoost had the highest accuracy, Random Forest provided the best balance for the business objective:

- Strong recall for identifying cancellations
- Better F1 score than Logistic Regression and XGBoost
- Highest ROC-AUC among the compared models
- Better balance between identifying high-risk bookings and avoiding excessive false positives

For cancellation-risk use cases, recall and F1 score are important because missed cancellations can lead to unexpected revenue loss.

### Prediction Output Findings

Prediction output file:

- `data/ml/fact_booking_predictions.csv`

| Metric | Value |
|---|---:|
| Prediction rows | 86,638 |
| Model name | Random Forest |
| Model version | v1.0 |
| Average cancellation probability | 37.78% |
| Predicted cancelled bookings | 29,256 |
| Predicted cancellation rate | 33.77% |
| Total expected revenue at risk | 14.93M |

### Risk Level Findings

Risk levels were assigned from cancellation probability:

- Low Risk: probability below 30%
- Medium Risk: probability from 30% to below 70%
- High Risk: probability of 70% or above

| Risk Level | Bookings | Average Probability | Expected Revenue at Risk | Booking Value |
|---|---:|---:|---:|---:|
| High Risk | 15,558 | 81.45% | 6.86M | 8.38M |
| Medium Risk | 31,132 | 48.55% | 6.49M | 13.10M |
| Low Risk | 39,948 | 12.37% | 1.58M | 12.97M |

### Key Findings

- High Risk bookings represent a smaller share of bookings but carry a large expected revenue-at-risk amount.
- Medium Risk bookings contribute almost as much expected revenue at risk as High Risk bookings because the group is larger.
- Low Risk bookings still have some expected revenue at risk because probability-based risk is never zero.
- The prediction table can support targeted follow-up actions, overbooking strategy, cancellation monitoring, and revenue protection.

## Business Recommendations

### 1. Monitor Online TA Bookings Closely

Online TA is the largest segment and has a high cancellation rate of `35.55%`. Hotels should monitor this segment carefully and consider confirmation reminders, stricter cancellation policies, or targeted follow-up for high-risk reservations.

### 2. Focus Cancellation Controls on Long Lead-Time Bookings

Cancellation rate increases as lead time increases. Bookings made more than 180 days before arrival show cancellation rates close to or above `40%`. Long lead-time bookings should be flagged for additional monitoring.

### 3. Prioritize Peak Season Revenue Protection

July and August generate the strongest demand and revenue, but they also show elevated cancellation rates. During these months, cancellation risk management can have a larger revenue impact.

### 4. Use Special Requests as an Intent Signal

Bookings with more special requests tend to have lower cancellation rates. The number of special requests can be used as a useful indicator of guest commitment.

### 5. Operationalize the Prediction Output

The prediction output should be used to prioritize:

- High-risk booking follow-up
- Expected revenue-at-risk tracking
- Segment-level cancellation monitoring
- Power BI risk dashboards
- AI SQL chatbot answers for business users

## Limitations

- The dataset is historical and may not reflect current hotel demand patterns.
- Some variables may only be known later in the booking lifecycle, so care is needed before using them for real-time prediction.
- The model was evaluated on the available dataset and should be validated with fresh booking data before production use.
- The SQL chatbot should use read-only database access and stricter SQL validation before being exposed to external users.

## Conclusion

The exploration shows that hotel cancellation risk is concentrated in specific business areas: City Hotel, Online TA, transient customers, long lead-time bookings, and peak travel months. Revenue is strongest in July and August, but those months also carry significant cancellation exposure.

The Random Forest prediction model extends the analytics layer by estimating booking-level cancellation probability and expected revenue at risk. Combined with PostgreSQL, Power BI, and the LangChain SQL chatbot, this project provides a complete analytics workflow from raw data ingestion to business reporting and AI-assisted decision support.
