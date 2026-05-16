# Bronze Layer

The Bronze layer stores the raw hotel booking dataset with minimal changes.  
No business cleaning is applied at this stage.

The purpose of the Bronze layer is to preserve the original source data for traceability and auditing.

## Metadata Added

- `ingestion_timestamp`
- `source_file_name`
- `batch_id`

## Notes

Data quality issues such as missing values, duplicate records, zero guests, zero nights, and unusual ADR values are not fixed in the Bronze layer. These issues will be handled in the Silver layer.
