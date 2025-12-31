-- Rowcounts por partición (SparkSQL)
SELECT
  <partition_col>,
  COUNT(*) AS cnt
FROM <table>
GROUP BY <partition_col>
ORDER BY <partition_col>;
