"""
Financial Data ETL Pipeline
Extracts stock and commodity data, transforms it, and loads into PostgreSQL
Compatible with AI agent analysis workflows
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from sqlalchemy import create_engine, text
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'financial_data',
    'user': 'etl_user',
    'password': 'secure_password_here'
}

# Data source configurations
STOCK_SYMBOLS = {
    'US': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
    'Turkish': ['THYAO.IS', 'SISE.IS', 'KCHOL.IS', 'GARAN.IS', 'AKBNK.IS']
}

COMMODITY_SYMBOLS = {
    'Metals': ['GC=F', 'SI=F', 'CL=F'],  # Gold, Silver, Crude Oil
    'Currency': ['EURUSD=X', 'GBPUSD=X', 'USDTRY=X']  # EUR/USD, GBP/USD, USD/TRY
}

LOOKBACK_DAYS = 365  # Default 1 year of historical data

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

class DatabaseManager:
    """Handle all database operations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.engine = self._create_engine()
        self.conn = None
        
    def _create_engine(self):
        """Create SQLAlchemy engine"""
        connection_string = f"postgresql://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        return create_engine(connection_string)
    
    def connect(self):
        """Create database connection"""
        self.conn = psycopg2.connect(**self.config)
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def asset_exists(self, symbol: str) -> bool:
        """Check if asset exists in database"""
        query = "SELECT asset_id FROM markets.assets WHERE symbol = %s"
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'symbol': symbol})
            return result.fetchone() is not None
    
    def insert_asset(self, symbol: str, asset_name: str, asset_type: str, 
                    market: str, currency: str = 'USD', sector: str = None) -> int:
        """Insert new asset and return asset_id"""
        query = """
            INSERT INTO markets.assets (symbol, asset_name, asset_type, market, currency, sector)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO NOTHING
            RETURNING asset_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (symbol, asset_name, asset_type, market, currency, sector))
        result = cursor.fetchone()
        self.conn.commit()
        
        if result:
            return result[0]
        else:
            # Get existing asset_id
            cursor.execute("SELECT asset_id FROM markets.assets WHERE symbol = %s", (symbol,))
            return cursor.fetchone()[0]
    
    def insert_daily_prices(self, data: pd.DataFrame, asset_id: int):
        """Insert daily price data"""
        query = """
            INSERT INTO markets.daily_prices 
            (asset_id, price_date, open_price, close_price, high_price, low_price, volume, adjusted_close)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asset_id, price_date) DO UPDATE SET
            open_price = EXCLUDED.open_price,
            close_price = EXCLUDED.close_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            volume = EXCLUDED.volume,
            adjusted_close = EXCLUDED.adjusted_close
        """
        
        cursor = self.conn.cursor()
        records = []
        
        for date, row in data.iterrows():
            records.append((
                asset_id,
                date.date(),
                float(row['Open']) if pd.notna(row['Open']) else None,
                float(row['Close']) if pd.notna(row['Close']) else None,
                float(row['High']) if pd.notna(row['High']) else None,
                float(row['Low']) if pd.notna(row['Low']) else None,
                int(row['Volume']) if pd.notna(row['Volume']) else None,
                float(row['Adj Close']) if pd.notna(row['Adj Close']) else None,
            ))
        
        execute_batch(cursor, query, records, page_size=1000)
        self.conn.commit()
        logger.info(f"Inserted {len(records)} price records for asset_id {asset_id}")
    
    def insert_technical_indicators(self, asset_id: int, indicators_df: pd.DataFrame):
        """Insert technical indicators"""
        query = """
            INSERT INTO markets.technical_indicators
            (asset_id, price_date, sma_20, sma_50, sma_200, ema_12, ema_26, rsi_14, 
             macd, macd_signal, bollinger_upper, bollinger_middle, bollinger_lower, atr_14)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asset_id, price_date) DO UPDATE SET
            sma_20 = EXCLUDED.sma_20,
            sma_50 = EXCLUDED.sma_50,
            sma_200 = EXCLUDED.sma_200,
            ema_12 = EXCLUDED.ema_12,
            ema_26 = EXCLUDED.ema_26,
            rsi_14 = EXCLUDED.rsi_14,
            macd = EXCLUDED.macd,
            macd_signal = EXCLUDED.macd_signal,
            bollinger_upper = EXCLUDED.bollinger_upper,
            bollinger_middle = EXCLUDED.bollinger_middle,
            bollinger_lower = EXCLUDED.bollinger_lower,
            atr_14 = EXCLUDED.atr_14
        """
        
        cursor = self.conn.cursor()
        records = []
        
        for date, row in indicators_df.iterrows():
            records.append((
                asset_id,
                date.date(),
                float(row['SMA_20']) if pd.notna(row['SMA_20']) else None,
                float(row['SMA_50']) if pd.notna(row['SMA_50']) else None,
                float(row['SMA_200']) if pd.notna(row['SMA_200']) else None,
                float(row['EMA_12']) if pd.notna(row['EMA_12']) else None,
                float(row['EMA_26']) if pd.notna(row['EMA_26']) else None,
                float(row['RSI_14']) if pd.notna(row['RSI_14']) else None,
                float(row['MACD']) if pd.notna(row['MACD']) else None,
                float(row['MACD_Signal']) if pd.notna(row['MACD_Signal']) else None,
                float(row['BB_Upper']) if pd.notna(row['BB_Upper']) else None,
                float(row['BB_Middle']) if pd.notna(row['BB_Middle']) else None,
                float(row['BB_Lower']) if pd.notna(row['BB_Lower']) else None,
                float(row['ATR_14']) if pd.notna(row['ATR_14']) else None,
            ))
        
        execute_batch(cursor, query, records, page_size=1000)
        self.conn.commit()
        logger.info(f"Inserted {len(records)} technical indicator records for asset_id {asset_id}")
    
    def log_etl_job(self, asset_id: int, job_name: str, job_type: str, 
                   status: str, rows_processed: int, rows_failed: int = 0, 
                   error_message: str = None, duration_seconds: int = None):
        """Log ETL job execution"""
        query = """
            INSERT INTO markets.etl_logs 
            (asset_id, job_name, job_type, status, rows_processed, rows_failed, error_message, 
             started_at, completed_at, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (asset_id, job_name, job_type, status, rows_processed, 
                              rows_failed, error_message, duration_seconds))
        self.conn.commit()

# ============================================================================
# DATA EXTRACTION & TRANSFORMATION
# ============================================================================

class TechnicalIndicatorCalculator:
    """Calculate technical indicators for price data"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_12 = data.ewm(span=12, adjust=False).mean()
        ema_26 = data.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, 
                                  std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @classmethod
    def calculate_all_indicators(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators and return enriched dataframe"""
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        indicators = pd.DataFrame(index=df.index)
        indicators['SMA_20'] = cls.calculate_sma(close, 20)
        indicators['SMA_50'] = cls.calculate_sma(close, 50)
        indicators['SMA_200'] = cls.calculate_sma(close, 200)
        indicators['EMA_12'] = cls.calculate_ema(close, 12)
        indicators['EMA_26'] = cls.calculate_ema(close, 26)
        indicators['RSI_14'] = cls.calculate_rsi(close, 14)
        
        macd, signal = cls.calculate_macd(close)
        indicators['MACD'] = macd
        indicators['MACD_Signal'] = signal
        
        bb_upper, bb_middle, bb_lower = cls.calculate_bollinger_bands(close, 20, 2.0)
        indicators['BB_Upper'] = bb_upper
        indicators['BB_Middle'] = bb_middle
        indicators['BB_Lower'] = bb_lower
        
        indicators['ATR_14'] = cls.calculate_atr(high, low, close, 14)
        
        return indicators

class DataExtractor:
    """Extract data from Yahoo Finance"""
    
    @staticmethod
    def fetch_historical_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical price data from Yahoo Finance"""
        try:
            logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                logger.warning(f"No data retrieved for {symbol}")
                return pd.DataFrame()
            
            logger.info(f"Retrieved {len(data)} records for {symbol}")
            return data
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

# ============================================================================
# MAIN ETL PIPELINE
# ============================================================================

class FinancialETLPipeline:
    """Main ETL orchestration"""
    
    def __init__(self, db_config: Dict):
        self.db = DatabaseManager(db_config)
        self.extractor = DataExtractor()
        self.indicator_calc = TechnicalIndicatorCalculator()
        
    def run_full_pipeline(self, symbols_by_category: Dict[str, List[str]], 
                         lookback_days: int = 365):
        """Execute full ETL pipeline for all symbols"""
        self.db.connect()
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            for category, symbols in symbols_by_category.items():
                for symbol in symbols:
                    self._process_symbol(symbol, category, start_date, end_date)
        
        finally:
            self.db.disconnect()
    
    def _process_symbol(self, symbol: str, category: str, start_date: str, end_date: str):
        """Process individual symbol"""
        job_start = datetime.now()
        
        try:
            # Extract
            logger.info(f"Processing {symbol} (Category: {category})")
            raw_data = self.extractor.fetch_historical_data(symbol, start_date, end_date)
            
            if raw_data.empty:
                self.db.log_etl_job(None, symbol, 'daily_update', 'failed', 0, 
                                   error_message=f"No data retrieved for {symbol}")
                return
            
            # Ensure or create asset
            if not self.db.asset_exists(symbol):
                asset_id = self.db.insert_asset(symbol, symbol, 'stock', 'Various', 'USD', category)
                logger.info(f"Created new asset: {symbol} (ID: {asset_id})")
            else:
                with self.db.engine.connect() as conn:
                    result = conn.execute(text("SELECT asset_id FROM markets.assets WHERE symbol = :symbol"), 
                                        {'symbol': symbol})
                    asset_id = result.fetchone()[0]
            
            # Transform - Load price data
            self.db.insert_daily_prices(raw_data, asset_id)
            
            # Transform - Calculate indicators
            indicators = self.indicator_calc.calculate_all_indicators(raw_data)
            self.db.insert_technical_indicators(asset_id, indicators)
            
            # Log success
            duration = (datetime.now() - job_start).total_seconds()
            self.db.log_etl_job(asset_id, symbol, 'daily_update', 'success', 
                               len(raw_data), duration_seconds=int(duration))
            
            logger.info(f"Successfully processed {symbol}: {len(raw_data)} records")
        
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
            duration = (datetime.now() - job_start).total_seconds()
            self.db.log_etl_job(None, symbol, 'daily_update', 'failed', 0, 
                               error_message=str(e), duration_seconds=int(duration))

# ============================================================================
# QUERY HELPERS FOR AGENTS
# ============================================================================

class AgentDataProvider:
    """Provide formatted data for AI agents"""
    
    def __init__(self, db_config: Dict):
        self.engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
    
    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        """Get latest prices for symbols"""
        query = """
            SELECT 
                a.symbol, a.asset_name, a.asset_type,
                dp.price_date, dp.open_price, dp.close_price, 
                dp.high_price, dp.low_price, dp.volume,
                ROUND(((dp.close_price - LAG(dp.close_price) OVER (PARTITION BY a.asset_id ORDER BY dp.price_date)) 
                    / LAG(dp.close_price) OVER (PARTITION BY a.asset_id ORDER BY dp.price_date) * 100)::numeric, 2) as daily_change_pct
            FROM markets.assets a
            JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
            WHERE a.symbol IN ({})
            AND dp.price_date = (SELECT MAX(price_date) FROM markets.daily_prices WHERE asset_id = a.asset_id)
        """.format(','.join([f"'{s}'" for s in symbols]))
        
        return pd.read_sql(query, self.engine)
    
    def get_historical_data(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """Get historical data for pattern analysis"""
        query = """
            SELECT 
                a.symbol, a.asset_name,
                dp.price_date, dp.open_price, dp.close_price, 
                dp.high_price, dp.low_price, dp.volume,
                ti.sma_20, ti.sma_50, ti.sma_200,
                ti.rsi_14, ti.macd, ti.atr_14
            FROM markets.assets a
            JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
            LEFT JOIN markets.technical_indicators ti ON a.asset_id = ti.asset_id AND dp.price_date = ti.price_date
            WHERE a.symbol = %s
            AND dp.price_date >= CURRENT_DATE - INTERVAL '{} days'
            ORDER BY dp.price_date DESC
        """.format(days)
        
        return pd.read_sql(query, self.engine, params=(symbol,))
    
    def detect_golden_cross(self, symbol: str) -> Dict:
        """Detect Golden Cross pattern (SMA50 crosses above SMA200)"""
        query = """
            SELECT 
                dp.price_date,
                ti.sma_50,
                ti.sma_200,
                LAG(ti.sma_50) OVER (ORDER BY dp.price_date) as prev_sma_50,
                LAG(ti.sma_200) OVER (ORDER BY dp.price_date) as prev_sma_200
            FROM markets.assets a
            JOIN markets.daily_prices dp ON a.asset_id = dp.asset_id
            JOIN markets.technical_indicators ti ON a.asset_id = ti.asset_id AND dp.price_date = ti.price_date
            WHERE a.symbol = %s
            AND dp.price_date >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY dp.price_date DESC
            LIMIT 50
        """
        
        df = pd.read_sql(query, self.engine, params=(symbol,))
        
        # Detect cross
        for idx, row in df.iterrows():
            if (row['prev_sma_50'] is not None and row['prev_sma_200'] is not None):
                if (row['prev_sma_50'] <= row['prev_sma_200'] and 
                    row['sma_50'] > row['sma_200']):
                    return {
                        'symbol': symbol,
                        'pattern': 'Golden Cross',
                        'date': row['price_date'],
                        'sma_50': float(row['sma_50']),
                        'sma_200': float(row['sma_200']),
                        'confidence': 0.85
                    }
        
        return None

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Initialize and run ETL pipeline
    pipeline = FinancialETLPipeline(DB_CONFIG)
    
    # Combine all symbols
    all_symbols = {
        **STOCK_SYMBOLS,
        **COMMODITY_SYMBOLS
    }
    
    # Run full pipeline
    pipeline.run_full_pipeline(all_symbols, lookback_days=LOOKBACK_DAYS)
    
    logger.info("ETL Pipeline execution completed")
    
    # Example: Use AgentDataProvider for agent queries
    provider = AgentDataProvider(DB_CONFIG)
    print("\n=== Latest Prices ===")
    print(provider.get_latest_prices(['AAPL', 'GOLD', 'USDTRY=X']))
    
    print("\n=== Golden Cross Detection ===")
    cross = provider.detect_golden_cross('AAPL')
    print(json.dumps(cross, indent=2, default=str))