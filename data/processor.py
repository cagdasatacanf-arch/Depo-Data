"""
Data processing and statistical analysis utilities
"""
import pandas as pd
import numpy as np
from typing import Dict, List


class DataProcessor:
    """Process and analyze commodity price data"""
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame, commodity_name: str) -> Dict:
        """
        Calculate statistical summary for commodity price data
        
        Args:
            df: DataFrame with 'Year' and 'price' columns
            commodity_name: Name of the commodity
            
        Returns:
            Dictionary with statistical metrics
        """
        prices = df['price'].values
        years = df['Year'].values
        
        # Find min/max with their years
        min_idx = prices.argmin()
        max_idx = prices.argmax()
        
        # Calculate total change percentage
        if len(prices) > 1:
            total_change_pct = ((prices[-1] - prices[0]) / prices[0]) * 100
        else:
            total_change_pct = 0.0
        
        # Calculate volatility (coefficient of variation)
        mean_price = prices.mean()
        volatility = (prices.std() / mean_price) * 100 if mean_price != 0 else 0.0
        
        return {
            'commodity': commodity_name,
            'mean': float(prices.mean()),
            'median': float(np.median(prices)),
            'std_dev': float(prices.std()),
            'min_price': float(prices[min_idx]),
            'max_price': float(prices[max_idx]),
            'min_year': int(years[min_idx]),
            'max_year': int(years[max_idx]),
            'total_change_pct': float(total_change_pct),
            'volatility': float(volatility)
        }
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate year-over-year returns
        
        Args:
            df: DataFrame with 'Year' and 'price' columns
            
        Returns:
            DataFrame with additional 'returns' column
        """
        result = df.copy()
        result['returns'] = result['price'].pct_change() * 100
        return result
    
    @staticmethod
    def calculate_moving_average(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """
        Calculate moving average
        
        Args:
            df: DataFrame with 'Year' and 'price' columns
            window: Window size for moving average
            
        Returns:
            DataFrame with additional 'ma' column
        """
        result = df.copy()
        result['ma'] = result['price'].rolling(window=window).mean()
        return result
    
    @staticmethod
    def normalize_prices(df: pd.DataFrame, base_year: int = None) -> pd.DataFrame:
        """
        Normalize prices to a base year (base year = 100)
        
        Args:
            df: DataFrame with 'Year' and 'price' columns
            base_year: Base year for normalization (default: first year)
            
        Returns:
            DataFrame with additional 'normalized' column
        """
        result = df.copy()
        
        if base_year is None:
            base_price = result['price'].iloc[0]
        else:
            base_row = result[result['Year'] == base_year]
            if base_row.empty:
                raise ValueError(f"Base year {base_year} not found in data")
            base_price = base_row['price'].iloc[0]
        
        result['normalized'] = (result['price'] / base_price) * 100
        return result
    
    @staticmethod
    def aggregate_by_decade(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate data by decade
        
        Args:
            df: DataFrame with 'Year' and 'price' columns
            
        Returns:
            DataFrame with decade averages
        """
        result = df.copy()
        result['decade'] = (result['Year'] // 10) * 10
        
        aggregated = result.groupby('decade').agg({
            'price': ['mean', 'min', 'max', 'std']
        }).reset_index()
        
        aggregated.columns = ['decade', 'mean_price', 'min_price', 'max_price', 'std_price']
        return aggregated
    
    @staticmethod
    def calculate_correlation(df: pd.DataFrame, commodities: List[str]) -> pd.DataFrame:
        """
        Calculate correlation matrix between commodities
        
        Args:
            df: DataFrame with Year and commodity columns
            commodities: List of commodity names to correlate
            
        Returns:
            Correlation matrix as DataFrame
        """
        # Select only the commodity columns
        price_data = df[commodities]
        
        # Calculate correlation
        correlation = price_data.corr()
        
        return correlation
    
    @staticmethod
    def calculate_growth_rate(df: pd.DataFrame) -> Dict:
        """
        Calculate compound annual growth rate (CAGR)
        
        Args:
            df: DataFrame with 'Year' and 'price' columns
            
        Returns:
            Dictionary with CAGR and related metrics
        """
        if len(df) < 2:
            return {'cagr': 0.0, 'total_years': 0}
        
        start_price = df['price'].iloc[0]
        end_price = df['price'].iloc[-1]
        start_year = df['Year'].iloc[0]
        end_year = df['Year'].iloc[-1]
        
        years = end_year - start_year
        
        if years == 0 or start_price <= 0:
            return {'cagr': 0.0, 'total_years': years}
        
        # CAGR formula: (End Value / Start Value)^(1/years) - 1
        cagr = (pow(end_price / start_price, 1 / years) - 1) * 100
        
        return {
            'cagr': float(cagr),
            'total_years': int(years),
            'start_price': float(start_price),
            'end_price': float(end_price),
            'start_year': int(start_year),
            'end_year': int(end_year)
        }
