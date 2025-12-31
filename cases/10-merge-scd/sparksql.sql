-- Delta Lake (si aplica)
MERGE INTO dim_customer t
USING stg_customer s
ON t.customer_id = s.customer_id
WHEN MATCHED THEN UPDATE SET name = s.name, updated_at = current_timestamp()
WHEN NOT MATCHED THEN INSERT (customer_id, name, updated_at)
VALUES (s.customer_id, s.name, current_timestamp());
