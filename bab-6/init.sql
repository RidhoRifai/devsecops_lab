CREATE SCHEMA IF NOT EXISTS logs;
CREATE TABLE logs.fluentbit (
  id BIGSERIAL PRIMARY KEY,
  tag VARCHAR(200),
  time TIMESTAMP,
  data JSONB
);
CREATE INDEX idx_fb_time ON logs.fluentbit(time);
CREATE INDEX idx_fb_tag ON logs.fluentbit(tag);
CREATE INDEX idx_fb_data ON logs.fluentbit USING GIN(data);
CREATE OR REPLACE VIEW logs.recent_logs AS
SELECT id, time, tag,
       REPLACE(data->>'container_name', '/', '') AS container,
       data->>'source' AS source,
       LEFT(data->>'log', 200) AS preview
FROM logs.fluentbit
ORDER BY time DESC
LIMIT 100;
