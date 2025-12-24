-- ============================================================================
-- Financial Database Schema - PostgreSQL
-- For Stock Market & Commodity Pattern Analysis with AI Agents
-- ============================================================================

-- Create database
CREATE DATABASE financial_data;
\c financial_data;

-- ============================================================================
-- SCHEMAS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS markets;
CREATE SCHEMA IF NOT EXISTS analysis;

-- ============================================================================
-- CORE TABLES - MARKETS SCHEMA
-- ============================================================================

-- Table: Assets (stocks and commodities)
CREATE TABLE markets.assets (
    asset_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    asset_name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('stock', 'commodity')),
    market VARCHAR(50), -- NYSE, NASDAQ, TCE (Turkish), commodity exchange
    currency VARCHAR(10) DEFAULT 'USD',
    sector VARCHAR(100), -- for stocks
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_assets_symbol ON markets.assets(symbol);
CREATE INDEX idx_assets_type ON markets.assets(asset_type);
CREATE INDEX idx_assets_market ON markets.assets(market);

-- Table: Daily Price Data (optimized for time-series queries)
CREATE TABLE markets.daily_prices (
    price_id BIGSERIAL PRIMARY KEY,
    asset_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    price_date DATE NOT NULL,
    open_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    volume BIGINT,
    adjusted_close DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, price_date)
);

-- Optimized indexes for common queries
CREATE INDEX idx_daily_prices_asset_date ON markets.daily_prices(asset_id, price_date DESC) 
    USING BRIN; -- Block Range Index for time-series
CREATE INDEX idx_daily_prices_date ON markets.daily_prices(price_date DESC);

-- Table: Technical Indicators (calculated metrics)
CREATE TABLE markets.technical_indicators (
    indicator_id BIGSERIAL PRIMARY KEY,
    asset_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    price_date DATE NOT NULL,
    sma_20 DECIMAL(20,8),      -- Simple Moving Average 20 days
    sma_50 DECIMAL(20,8),      -- Simple Moving Average 50 days
    sma_200 DECIMAL(20,8),     -- Simple Moving Average 200 days
    ema_12 DECIMAL(20,8),      -- Exponential Moving Average 12 days
    ema_26 DECIMAL(20,8),      -- Exponential Moving Average 26 days
    rsi_14 DECIMAL(5,2),       -- Relative Strength Index
    macd DECIMAL(20,8),        -- MACD line
    macd_signal DECIMAL(20,8), -- MACD signal line
    bollinger_upper DECIMAL(20,8),
    bollinger_middle DECIMAL(20,8),
    bollinger_lower DECIMAL(20,8),
    atr_14 DECIMAL(20,8),      -- Average True Range
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, price_date)
);

CREATE INDEX idx_indicators_asset_date ON markets.technical_indicators(asset_id, price_date DESC);

-- Table: Market Events (dividends, splits, earnings)
CREATE TABLE markets.market_events (
    event_id SERIAL PRIMARY KEY,
    asset_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('dividend', 'split', 'earnings', 'announcement')),
    event_value DECIMAL(20,8), -- dividend amount or split ratio
    event_description TEXT,
    impact_level VARCHAR(20), -- low, medium, high
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_asset_date ON markets.market_events(asset_id, event_date DESC);

-- Table: Intraday Data (optional, for minute/hourly analysis)
CREATE TABLE markets.intraday_prices (
    intraday_id BIGSERIAL PRIMARY KEY,
    asset_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    price_datetime TIMESTAMP NOT NULL,
    open_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, price_datetime)
);

CREATE INDEX idx_intraday_asset_time ON markets.intraday_prices(asset_id, price_datetime DESC) USING BRIN;

-- ============================================================================
-- ANALYSIS TABLES
-- ============================================================================

-- Table: Pattern Detection Results
CREATE TABLE analysis.detected_patterns (
    pattern_id BIGSERIAL PRIMARY KEY,
    asset_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    pattern_type VARCHAR(100), -- 'golden_cross', 'death_cross', 'double_bottom', etc
    detected_date DATE NOT NULL,
    confidence_score DECIMAL(5,2), -- 0-100
    pattern_start_date DATE,
    pattern_end_date DATE,
    description TEXT,
    agent_id VARCHAR(100), -- which agent detected this
    analysis_notes JSONB, -- flexible field for agent analysis
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_patterns_asset_date ON analysis.detected_patterns(asset_id, detected_date DESC);
CREATE INDEX idx_patterns_type ON analysis.detected_patterns(pattern_type);

-- Table: Agent Analysis Results
CREATE TABLE analysis.agent_reports (
    report_id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    asset_id INT REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    analysis_type VARCHAR(100), -- 'trend', 'volatility', 'correlation', etc
    summary TEXT,
    confidence_score DECIMAL(5,2),
    recommendations JSONB, -- flexible structure for agent recommendations
    data_snapshot JSONB, -- snapshot of data analyzed
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reports_agent_date ON analysis.agent_reports(agent_name, analysis_date DESC);
CREATE INDEX idx_reports_asset ON analysis.agent_reports(asset_id);

-- Table: Price Correlations
CREATE TABLE analysis.correlations (
    correlation_id BIGSERIAL PRIMARY KEY,
    asset_1_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    asset_2_id INT NOT NULL REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    correlation_date DATE NOT NULL,
    correlation_coefficient DECIMAL(5,4), -- -1 to 1
    lookback_days INT DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_1_id, asset_2_id, correlation_date)
);

CREATE INDEX idx_correlations_date ON analysis.correlations(correlation_date DESC);

-- ============================================================================
-- METADATA TABLES
-- ============================================================================

-- Table: Data Sources
CREATE TABLE markets.data_sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100),
    api_provider VARCHAR(100), -- 'yfinance', 'alphavantage', 'finnhub', etc
    api_endpoint VARCHAR(500),
    rate_limit INT, -- requests per minute
    last_update TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

-- Table: ETL Job Logs
CREATE TABLE markets.etl_logs (
    log_id BIGSERIAL PRIMARY KEY,
    asset_id INT REFERENCES markets.assets(asset_id) ON DELETE CASCADE,
    job_name VARCHAR(100),
    job_type VARCHAR(50), -- 'daily_update', 'historical_load', 'indicator_calc'
    status VARCHAR(20), -- 'success', 'failed', 'in_progress'
    rows_processed INT,
    rows_failed INT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INT
);

CREATE INDEX idx_etl_logs_date ON markets.etl_logs(started_at DESC);

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- Latest prices for all assets
CREATE VIEW markets.vw_latest_prices AS
SELECT 
    a.symbol,
    a.asset_name,
    a.asset_type,
    dp.price_date,
    dp.open_price,
    dp.close_price,
    dp.high_price,
    dp.low_price,
    dp.volume,
    ROUND(((dp.close_price - dp.open_price) / dp.open_price * 100)::numeric, 2) as daily_change_pct
FROM markets.assets a
JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
WHERE dp.price_date = (SELECT MAX(price_date) FROM markets.daily_prices WHERE asset_id = a.asset_id);

-- Recent price movements
CREATE VIEW markets.vw_price_movements AS
SELECT 
    a.symbol,
    a.asset_name,
    dp1.price_date as last_date,
    dp1.close_price as last_close,
    ROUND(((dp1.close_price - dp2.close_price) / dp2.close_price * 100)::numeric, 2) as change_5d_pct,
    ROUND(((dp1.close_price - dp3.close_price) / dp3.close_price * 100)::numeric, 2) as change_30d_pct,
    ROUND(((dp1.close_price - dp4.close_price) / dp4.close_price * 100)::numeric, 2) as change_90d_pct,
    dp1.volume as recent_volume
FROM markets.assets a
JOIN markets.daily_prices dp1 ON a.asset_id = dp1.asset_id
LEFT JOIN markets.daily_prices dp2 ON a.asset_id = dp2.asset_id AND dp2.price_date = dp1.price_date - INTERVAL '5 days'
LEFT JOIN markets.daily_prices dp3 ON a.asset_id = dp3.asset_id AND dp3.price_date = dp1.price_date - INTERVAL '30 days'
LEFT JOIN markets.daily_prices dp4 ON a.asset_id = dp4.asset_id AND dp4.price_date = dp1.price_date - INTERVAL '90 days'
WHERE dp1.price_date = (SELECT MAX(price_date) FROM markets.daily_prices WHERE asset_id = a.asset_id);

-- Volatility analysis
CREATE VIEW analysis.vw_volatility_analysis AS
SELECT 
    a.symbol,
    a.asset_name,
    MAX(dp.price_date) as analysis_date,
    ROUND(STDDEV(dp.close_price)::numeric, 2) as volatility_30d,
    ROUND(AVG(dp.close_price)::numeric, 2) as avg_price_30d,
    ROUND((MAX(dp.close_price) - MIN(dp.close_price))::numeric, 2) as price_range_30d
FROM markets.assets a
JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
WHERE dp.price_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.asset_id, a.symbol, a.asset_name;

-- ============================================================================
-- FUNCTIONS FOR COMMON OPERATIONS
-- ============================================================================

-- Function to calculate simple moving average
CREATE OR REPLACE FUNCTION markets.calculate_sma(
    p_asset_id INT,
    p_date DATE,
    p_days INT
) RETURNS DECIMAL AS $$
BEGIN
    RETURN (
        SELECT AVG(close_price)
        FROM markets.daily_prices
        WHERE asset_id = p_asset_id
        AND price_date <= p_date
        AND price_date > p_date - (p_days || ' days')::interval
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get price volatility
CREATE OR REPLACE FUNCTION markets.get_volatility(
    p_asset_id INT,
    p_days INT DEFAULT 30
) RETURNS DECIMAL AS $$
BEGIN
    RETURN (
        SELECT STDDEV(close_price)
        FROM markets.daily_prices
        WHERE asset_id = p_asset_id
        AND price_date >= CURRENT_DATE - (p_days || ' days')::interval
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA INSERTION
-- ============================================================================

-- Insert sample assets (you'll populate these with real data)
INSERT INTO markets.assets (symbol, asset_name, asset_type, market, currency, sector) VALUES
('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD', 'Technology'),
('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'USD', 'Technology'),
('GOLD', 'Gold Futures', 'commodity', 'COMEX', 'USD', 'Precious Metals'),
('CRUDE', 'WTI Crude Oil', 'commodity', 'NYMEX', 'USD', 'Energy'),
('EUR', 'Euro/Dollar', 'commodity', 'FOREX', 'USD', 'Currency'),
('THYAO', 'Turkish Airlines', 'stock', 'TCE', 'TRY', 'Airlines');

INSERT INTO markets.data_sources (source_name, api_provider) VALUES
('Yahoo Finance', 'yfinance'),
('Alpha Vantage', 'alphavantage'),
('IEX Cloud', 'iexcloud'),
('Finnhub', 'finnhub'),
('World Bank', 'world_bank');

-- ============================================================================
-- GRANTS (adjust user names as needed)
-- ============================================================================

-- Create read-only user for agents
CREATE USER agent_user WITH PASSWORD 'secure_password_here';
GRANT USAGE ON SCHEMA markets, analysis TO agent_user;
GRANT SELECT ON ALL TABLES IN SCHEMA markets TO agent_user;
GRANT SELECT ON ALL TABLES IN SCHEMA analysis TO agent_user;

-- Create read-write user for ETL
CREATE USER etl_user WITH PASSWORD 'secure_password_here';
GRANT USAGE ON SCHEMA markets, analysis TO etl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA markets TO etl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analysis TO etl_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA markets TO etl_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analysis TO etl_user;