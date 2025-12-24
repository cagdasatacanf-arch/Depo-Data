"""
Data loader for CSV commodity price data
"""
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and cache commodity price data from CSV files"""
    
    def __init__(self, data_path: str = "Database/data/commodity_prices.csv"):
        self.data_path = Path(data_path)
        self._data: Optional[pd.DataFrame] = None
        self._commodities: Optional[List[str]] = None
        
    def load_data(self) -> pd.DataFrame:
        """Load commodity price data from CSV"""
        if self._data is not None:
            return self._data
            
        try:
            logger.info(f"Loading data from {self.data_path}")
            self._data = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(self._data)} rows of data")
            return self._data
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def get_commodities(self) -> List[str]:
        """Get list of all available commodities"""
        if self._commodities is not None:
            return self._commodities
            
        df = self.load_data()
        # All columns except 'Year' are commodities
        self._commodities = [col for col in df.columns if col != 'Year']
        return self._commodities
    
    def get_commodity_data(
        self, 
        commodity: str, 
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get historical data for a specific commodity
        
        Args:
            commodity: Name of the commodity
            start_year: Optional start year filter
            end_year: Optional end year filter
            
        Returns:
            DataFrame with Year and price columns
        """
        df = self.load_data()
        
        if commodity not in df.columns:
            raise ValueError(f"Commodity '{commodity}' not found in dataset")
        
        # Select Year and commodity column
        result = df[['Year', commodity]].copy()
        result = result.rename(columns={commodity: 'price'})
        
        # Filter by year range
        if start_year is not None:
            result = result[result['Year'] >= start_year]
        if end_year is not None:
            result = result[result['Year'] <= end_year]
        
        # Remove rows with missing prices
        result = result.dropna(subset=['price'])
        
        return result
    
    def get_multiple_commodities(
        self,
        commodities: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get historical data for multiple commodities
        
        Args:
            commodities: List of commodity names
            start_year: Optional start year filter
            end_year: Optional end year filter
            
        Returns:
            DataFrame with Year column and one column per commodity
        """
        df = self.load_data()
        
        # Validate all commodities exist
        for commodity in commodities:
            if commodity not in df.columns:
                raise ValueError(f"Commodity '{commodity}' not found in dataset")
        
        # Select Year and requested commodities
        columns = ['Year'] + commodities
        result = df[columns].copy()
        
        # Filter by year range
        if start_year is not None:
            result = result[result['Year'] >= start_year]
        if end_year is not None:
            result = result[result['Year'] <= end_year]
        
        return result
    
    def get_date_range(self) -> Dict[str, int]:
        """Get the available date range in the dataset"""
        df = self.load_data()
        return {
            'start_year': int(df['Year'].min()),
            'end_year': int(df['Year'].max()),
            'total_years': len(df)
        }
    
    def get_commodity_info(self, commodity: str) -> Dict:
        """Get metadata about a commodity"""
        df = self.load_data()
        
        if commodity not in df.columns:
            raise ValueError(f"Commodity '{commodity}' not found in dataset")
        
        commodity_data = df[['Year', commodity]].dropna(subset=[commodity])
        
        return {
            'name': commodity,
            'available_from': int(commodity_data['Year'].min()),
            'available_to': int(commodity_data['Year'].max()),
            'data_points': len(commodity_data)
        }
