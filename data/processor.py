"""
Data processing and statistical analysis utilities
"""
from typing import Dict, List, Any
import statistics


class DataProcessor:
    """Process and analyze stock and metal price data"""
    
    @staticmethod
    def calculate_statistics(data_points: List[Dict[str, Any]], symbol: str) -> Dict:
        """
        Calculate statistical summary for OHLCV data
        
        Args:
            data_points: List of OHLCV data dictionaries
            symbol: Symbol code
            
        Returns:
            Dictionary with statistical metrics
        """
        if not data_points:
            raise ValueError("No data points provided")
        
        # Extract closing prices and dates
        closes = [float(point['close']) for point in data_points]
        dates = [point['date'] for point in data_points]
        
        # Find min/max with their dates
        min_price = min(closes)
        max_price = max(closes)
        min_idx = closes.index(min_price)
        max_idx = closes.index(max_price)
        
        # Calculate total change percentage
        if len(closes) > 1:
            total_change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100
        else:
            total_change_pct = 0.0
        
        # Calculate volatility (coefficient of variation)
        mean_price = statistics.mean(closes)
        std_dev = statistics.stdev(closes) if len(closes) > 1 else 0.0
        volatility = (std_dev / mean_price) * 100 if mean_price != 0 else 0.0
        
        return {
            'symbol': symbol,
            'mean_close': float(mean_price),
            'median_close': float(statistics.median(closes)),
            'std_dev': float(std_dev),
            'min_price': float(min_price),
            'max_price': float(max_price),
            'min_date': dates[min_idx],
            'max_date': dates[max_idx],
            'total_change_pct': float(total_change_pct),
            'volatility': float(volatility)
        }
    
    @staticmethod
    def calculate_returns(data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate day-to-day returns
        
        Args:
            data_points: List of OHLCV data dictionaries
            
        Returns:
            List with additional 'returns' field
        """
        result = []
        for i, point in enumerate(data_points):
            new_point = point.copy()
            if i > 0:
                prev_close = float(data_points[i-1]['close'])
                curr_close = float(point['close'])
                new_point['returns'] = ((curr_close - prev_close) / prev_close) * 100
            else:
                new_point['returns'] = 0.0
            result.append(new_point)
        return result
    
    @staticmethod
    def calculate_moving_average(data_points: List[Dict[str, Any]], window: int = 5) -> List[Dict[str, Any]]:
        """
        Calculate moving average
        
        Args:
            data_points: List of OHLCV data dictionaries
            window: Window size for moving average
            
        Returns:
            List with additional 'ma' field
        """
        result = []
        closes = [float(point['close']) for point in data_points]
        
        for i, point in enumerate(data_points):
            new_point = point.copy()
            if i >= window - 1:
                window_closes = closes[i - window + 1:i + 1]
                new_point['ma'] = statistics.mean(window_closes)
            else:
                new_point['ma'] = None
            result.append(new_point)
        return result
    
    @staticmethod
    def normalize_prices(data_points: List[Dict[str, Any]], base_date: str = None) -> List[Dict[str, Any]]:
        """
        Normalize prices to a base date (base date = 100)
        
        Args:
            data_points: List of OHLCV data dictionaries
            base_date: Base date for normalization (default: first date)
            
        Returns:
            List with additional 'normalized' field
        """
        if not data_points:
            return []
        
        # Find base price
        if base_date is None:
            base_price = float(data_points[0]['close'])
        else:
            base_point = next((p for p in data_points if p['date'] == base_date), None)
            if not base_point:
                raise ValueError(f"Base date {base_date} not found in data")
            base_price = float(base_point['close'])
        
        # Normalize all prices
        result = []
        for point in data_points:
            new_point = point.copy()
            new_point['normalized'] = (float(point['close']) / base_price) * 100
            result.append(new_point)
        return result
    
    @staticmethod
    def calculate_price_range(data_points: List[Dict[str, Any]]) -> Dict:
        """
        Calculate price range statistics
        
        Args:
            data_points: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with range statistics
        """
        if not data_points:
            return {}
        
        highs = [float(point['high']) for point in data_points]
        lows = [float(point['low']) for point in data_points]
        
        avg_range = statistics.mean([h - l for h, l in zip(highs, lows)])
        max_high = max(highs)
        min_low = min(lows)
        
        return {
            'average_daily_range': float(avg_range),
            'max_high': float(max_high),
            'min_low': float(min_low),
            'total_range': float(max_high - min_low)
        }
    
    @staticmethod
    def calculate_volume_stats(data_points: List[Dict[str, Any]]) -> Dict:
        """
        Calculate volume statistics (for stocks only)
        
        Args:
            data_points: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with volume statistics
        """
        volumes = [int(point['volume']) for point in data_points if 'volume' in point and point['volume'] is not None]
        
        if not volumes:
            return {
                'avg_volume': None,
                'max_volume': None,
                'min_volume': None
            }
        
        return {
            'avg_volume': int(statistics.mean(volumes)),
            'max_volume': max(volumes),
            'min_volume': min(volumes)
        }

