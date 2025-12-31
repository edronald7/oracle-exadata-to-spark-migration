MERGE INTO dim_customer t
USING stg_customer s
ON (t.customer_id = s.customer_id)
WHEN MATCHED THEN UPDATE SET t.name = s.name, t.updated_at = SYSDATE
WHEN NOT MATCHED THEN INSERT (customer_id, name, updated_at) VALUES (s.customer_id, s.name, SYSDATE);
