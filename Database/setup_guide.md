# Financial Database & n8n Integration Setup Guide

## Overview
This guide provides complete setup instructions for your SQL-based financial database that integrates with n8n workflows and Notion for AI agent pattern analysis.

---

## Part 1: Database Setup

### Prerequisites
- PostgreSQL 12+ installed
- Python 3.8+
- Git for version control

### Step 1: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Run the schema creation script
psql -U postgres -d postgres -f financial_db_setup.sql

# Verify creation
psql -U financial_data

# List tables
\dt markets.*
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
psycopg2-binary==2.9.9
pandas==2.1.3
sqlalchemy==2.0.23
yfinance==0.2.32
numpy==1.26.0
python-dateutil==2.8.2
requests==2.31.0
```

### Step 3: Configure Database Connection

Edit `etl_pipeline.py` and update:

```python
DB_CONFIG = {
    'host': 'your_postgres_host',
    'port': 5432,
    'database': 'financial_data',
    'user': 'etl_user',
    'password': 'your_secure_password'  # Change this!
}
```

---

## Part 2: Running the ETL Pipeline

### Manual Execution

```bash
# Run full pipeline
python etl_pipeline.py

# Check logs
tail -f etl_pipeline.log
```

### Scheduled Execution with Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Run daily at 7 PM
0 19 * * * cd /path/to/project && python etl_pipeline.py >> cron_etl.log 2>&1

# Run every 4 hours when agents are working
0 */4 * * * cd /path/to/project && python etl_pipeline.py >> cron_etl.log 2>&1
```

### Scheduled Execution with Task Scheduler (Windows)

1. Create batch file `run_etl.bat`:
```batch
@echo off
cd C:\path\to\project
python etl_pipeline.py
```

2. Open Task Scheduler
3. Create Basic Task → Set trigger (time/frequency)
4. Set action to run batch file

---

## Part 3: n8n Workflow Integration

### n8n Installation

```bash
# Using npm
npm install -g n8n

# Start n8n
n8n start

# Access at http://localhost:5678
```

### n8n Workflow: Daily Data Update

Create a new workflow in n8n with these nodes:

#### Node 1: Schedule Trigger
- **Type:** Cron
- **Expression:** `0 7 * * *` (7 AM daily)

#### Node 2: PostgreSQL - Execute Query
- **Type:** PostgreSQL
- **Host:** localhost
- **Port:** 5432
- **Database:** financial_data
- **User:** agent_user
- **Password:** [secure_password]

**Query:**
```sql
SELECT 
    a.symbol,
    a.asset_name,
    dp.price_date,
    dp.close_price,
    ti.sma_50,
    ti.sma_200,
    ti.rsi_14
FROM markets.assets a
JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
LEFT JOIN markets.technical_indicators ti ON a.asset_id = ti.asset_id AND dp.price_date = ti.price_date
WHERE dp.price_date = (SELECT MAX(price_date) FROM markets.daily_prices)
ORDER BY a.symbol
```

#### Node 3: Function (Filter Alerts)
```javascript
// Filter assets with interesting signals
const data = $input.all();
const alerts = [];

data.forEach(item => {
    // Golden Cross: SMA50 > SMA200
    if (item.sma_50 > item.sma_200 && item.sma_50 * 0.99 < item.sma_200) {
        alerts.push({
            symbol: item.symbol,
            signal: 'Golden Cross',
            price: item.close_price,
            confidence: 0.85
        });
    }
    
    // RSI Oversold
    if (item.rsi_14 < 30) {
        alerts.push({
            symbol: item.symbol,
            signal: 'Oversold (RSI < 30)',
            rsi: item.rsi_14,
            confidence: 0.75
        });
    }
});

return alerts;
```

#### Node 4: Notion - Create Database Item
- **Type:** Notion
- **Action:** Add database items
- **Database ID:** [Your Notion Database ID]

**Mapping:**
- Symbol → Ticker
- Signal → Pattern Type
- Price/RSI → Data
- Confidence → Confidence Score

**Notion Database Schema:**
```
- Ticker (Text)
- Pattern Type (Select)
- Date (Date)
- Price (Number)
- Confidence Score (Number 0-100)
- Status (Select: Pending, Analyzing, Complete)
```

#### Node 5: Slack Notification (Optional)
- **Type:** Slack
- **Message:**
```
🔔 *Financial Alert*
Symbol: {{$node["Function"].data[0].symbol}}
Signal: {{$node["Function"].data[0].signal}}
Confidence: {{$node["Function"].data[0].confidence}}
```

---

## Part 4: Notion Database Setup

### Database Structure for Agent Analysis

**Table 1: Assets Watchlist**
- Asset ID (Number)
- Symbol (Text)
- Asset Type (Select: Stock, Commodity)
- Market (Select)
- Last Price (Number)
- Last Updated (Date)
- Status (Select: Active, Inactive)

**Table 2: Pattern Detection**
- Pattern ID (Number)
- Symbol (Relation → Assets)
- Pattern Type (Select: Golden Cross, Death Cross, Oversold, Overbought, Breakout)
- Detection Date (Date)
- Price (Number)
- Confidence Score (Number 0-100)
- Agent Name (Text)
- Status (Select: New, Analyzing, Confirmed, False Alarm)
- Analysis Notes (Rich Text)
- Related Assets (Relation - for correlations)

**Table 3: Agent Reports**
- Report ID (Number)
- Agent Name (Text)
- Analysis Date (Date)
- Assets Analyzed (Relation → Assets)
- Analysis Type (Select: Trend, Volatility, Correlation, Prediction)
- Key Findings (Rich Text)
- Recommendations (Rich Text)
- Confidence Level (Number)
- Status (Select: Draft, Review, Published)

---

## Part 5: Query Examples for Agents

### Get Latest Price Data
```sql
SELECT symbol, asset_name, close_price, price_date
FROM markets.vw_latest_prices
ORDER BY symbol;
```

### Detect Golden Cross (SMA 50 > 200)
```sql
SELECT 
    a.symbol,
    dp.price_date,
    ti.sma_50,
    ti.sma_200,
    dp.close_price
FROM markets.assets a
JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
JOIN markets.technical_indicators ti ON a.asset_id = ti.asset_id AND dp.price_date = ti.price_date
WHERE ti.sma_50 > ti.sma_200
    AND LAG(ti.sma_50) OVER (PARTITION BY a.asset_id ORDER BY dp.price_date) <= LAG(ti.sma_200) OVER (PARTITION BY a.asset_id ORDER BY dp.price_date)
ORDER BY a.symbol, dp.price_date DESC;
```

### Get Volatility Analysis
```sql
SELECT * FROM analysis.vw_volatility_analysis
WHERE volatility_30d IS NOT NULL
ORDER BY volatility_30d DESC;
```

### Find Oversold Assets (RSI < 30)
```sql
SELECT 
    a.symbol,
    dp.close_price,
    ti.rsi_14,
    dp.price_date
FROM markets.assets a
JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
JOIN markets.technical_indicators ti ON a.asset_id = ti.asset_id AND dp.price_date = ti.price_date
WHERE ti.rsi_14 < 30
    AND dp.price_date = (SELECT MAX(price_date) FROM markets.daily_prices WHERE asset_id = a.asset_id)
ORDER BY ti.rsi_14;
```

### Get Price Movement Summary
```sql
SELECT * FROM markets.vw_price_movements
ORDER BY change_5d_pct DESC;
```

---

## Part 6: Agent Integration Best Practices

### 1. Agent Query Structure
```json
{
  "query_type": "pattern_detection",
  "symbol": "AAPL",
  "lookback_days": 90,
  "indicators": ["sma", "rsi", "macd", "bollinger"],
  "confidence_threshold": 0.75
}
```

### 2. Agent Response Format
```json
{
  "symbol": "AAPL",
  "patterns_detected": [
    {
      "pattern": "Golden Cross",
      "confidence": 0.85,
      "date": "2024-01-15",
      "description": "SMA50 crossed above SMA200",
      "recommendation": "Bullish signal - consider long position"
    }
  ],
  "analysis_date": "2024-01-16",
  "agent_id": "technical_analyzer_v1"
}
```

### 3. Agent Database Access Permissions
- Agents use `agent_user` (read-only)
- ETL uses `etl_user` (read-write)
- Never share production passwords in agent configs

### 4. Error Handling
```python
try:
    data = provider.get_historical_data(symbol, days=90)
    patterns = detect_patterns(data)
except Exception as e:
    logger.error(f"Agent analysis failed: {e}")
    # Store error in analysis table for review
```

---

## Part 7: Performance Optimization

### Index Strategy
The schema includes BRIN indexes for time-series data:
- Excellent performance for date-range queries
- Significantly smaller than BTREE indexes
- Ideal for append-only time-series data

### Query Optimization Tips
```sql
-- ❌ Slow: Full scan
SELECT * FROM markets.daily_prices WHERE symbol = 'AAPL';

-- ✅ Fast: Use indexed symbol + date
SELECT * FROM markets.daily_prices dp
JOIN markets.assets a ON dp.asset_id = a.asset_id
WHERE a.symbol = 'AAPL'
AND dp.price_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY dp.price_date DESC;

-- ✅ Fastest: Pre-computed views
SELECT * FROM markets.vw_latest_prices WHERE symbol = 'AAPL';
```

### Maintenance Tasks
```bash
# Weekly: Analyze table statistics
ANALYZE markets.daily_prices;

# Monthly: Vacuum and reindex
VACUUM ANALYZE markets.daily_prices;
REINDEX TABLE markets.daily_prices;

# Check table size
SELECT pg_size_pretty(pg_total_relation_size('markets.daily_prices'));
```

---

## Part 8: Monitoring & Alerts

### Check ETL Job Status
```sql
SELECT 
    job_name,
    status,
    rows_processed,
    error_message,
    completed_at
FROM markets.etl_logs
ORDER BY completed_at DESC
LIMIT 20;
```

### Monitor Data Freshness
```sql
SELECT 
    a.symbol,
    MAX(dp.price_date) as last_update,
    CURRENT_DATE - MAX(dp.price_date) as days_stale
FROM markets.assets a
JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
GROUP BY a.asset_id, a.symbol
ORDER BY days_stale DESC;
```

### Check Agent Report History
```sql
SELECT 
    agent_name,
    COUNT(*) as reports_generated,
    MAX(analysis_date) as last_analysis,
    AVG(confidence_score) as avg_confidence
FROM analysis.agent_reports
GROUP BY agent_name
ORDER BY last_analysis DESC;
```

---

## Part 9: Troubleshooting

### Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U etl_user -d financial_data -c "SELECT version();"

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql.log
```

### Data Issues
```sql
-- Check for missing dates (gaps in data)
WITH date_range AS (
    SELECT generate_series(
        (SELECT MIN(price_date) FROM markets.daily_prices),
        (SELECT MAX(price_date) FROM markets.daily_prices),
        '1 day'::interval
    )::date as date
)
SELECT dr.date
FROM date_range dr
WHERE NOT EXISTS (
    SELECT 1 FROM markets.daily_prices WHERE price_date = dr.date
)
AND EXTRACT(dow FROM dr.date) NOT IN (0, 6); -- Exclude weekends

-- Check for duplicate dates
SELECT asset_id, price_date, COUNT(*)
FROM markets.daily_prices
GROUP BY asset_id, price_date
HAVING COUNT(*) > 1;
```

### Performance Issues
```sql
-- Find slow queries
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check table bloat
SELECT 
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'markets'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Part 10: Backup & Recovery

### Automated Backups
```bash
#!/bin/bash
# backup_financial_db.sh
BACKUP_DIR="/backups/financial_db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
pg_dump -h localhost -U postgres financial_data | gzip > "$BACKUP_DIR/financial_data_$TIMESTAMP.sql.gz"

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup_financial_db.sh
```

### Restore from Backup
```bash
gunzip -c financial_data_YYYYMMDD_HHMMSS.sql.gz | psql -U postgres
```

---

## Quick Start Command Checklists

### Initial Setup (One-Time)
- [ ] Install PostgreSQL
- [ ] Run `financial_db_setup.sql`
- [ ] Install Python dependencies
- [ ] Configure `DB_CONFIG` in `etl_pipeline.py`
- [ ] Test database connection
- [ ] Run first ETL: `python etl_pipeline.py`

### n8n Integration Setup
- [ ] Install n8n
- [ ] Create daily update workflow
- [ ] Set up PostgreSQL connection
- [ ] Create Notion database
- [ ] Configure Notion integration node
- [ ] Test workflow manually
- [ ] Enable schedule

### Agent Setup
- [ ] Create `agent_user` in PostgreSQL
- [ ] Test agent read access
- [ ] Create sample query scripts
- [ ] Set up error logging
- [ ] Document agent APIs

---

## Support & Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- n8n Docs: https://docs.n8n.io/
- Notion API: https://developers.notion.com/
- yfinance: https://github.com/ranaroussi/yfinance
- SQLAlchemy: https://docs.sqlalchemy.org/

---

## Next Steps

1. Set up initial database with historical data (1-2 years)
2. Test ETL pipeline with daily runs
3. Create core n8n workflows for data updates
4. Build your agent analysis scripts using provided query examples
5. Configure Notion database for pattern tracking
6. Set up monitoring and alerts
7. Document your custom agents and workflows