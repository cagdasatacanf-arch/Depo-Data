"""
Data loader for JSON-based stock and metal data
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and cache stock and metal price data from JSON files"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.metadata_path = self.data_dir / "metadata.json"
        self._metadata: Optional[Dict] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def load_metadata(self) -> Dict:
        """Load metadata.json containing symbol definitions"""
        if self._metadata is not None:
            return self._metadata
            
        try:
            logger.info(f"Loading metadata from {self.metadata_path}")
            with open(self.metadata_path, 'r') as f:
                self._metadata = json.load(f)
            logger.info(f"Loaded {len(self._metadata.get('symbols', []))} symbols from metadata")
            return self._metadata
        except FileNotFoundError:
            logger.error(f"Metadata file not found: {self.metadata_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            raise
    
    def get_symbols(self) -> List[Dict[str, Any]]:
        """Get list of all available symbols with their metadata"""
        metadata = self.load_metadata()
        return metadata.get('symbols', [])
    
    def get_commodities(self) -> List[str]:
        """Get list of all available symbol names (for backward compatibility)"""
        symbols = self.get_symbols()
        return [s['symbol'] for s in symbols]
    
    def load_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """
        Load historical data for a specific symbol from its JSON file
        
        Args:
            symbol: Symbol code (e.g., 'AAPL', 'XAU')
            
        Returns:
            Dictionary containing symbol data
        """
        # Check cache first
        if symbol in self._cache:
            return self._cache[symbol]
        
        # Find symbol in metadata
        symbols = self.get_symbols()
        symbol_info = next((s for s in symbols if s['symbol'] == symbol), None)
        
        if not symbol_info:
            raise ValueError(f"Symbol '{symbol}' not found in metadata")
        
        # Load the data file
        data_path = self.data_dir / symbol_info['path']
        
        try:
            logger.info(f"Loading data for {symbol} from {data_path}")
            with open(data_path, 'r') as f:
                data = json.load(f)
            
            # Cache the data
            self._cache[symbol] = data
            logger.info(f"Loaded {len(data.get('data', []))} data points for {symbol}")
            return data
        except FileNotFoundError:
            logger.error(f"Data file not found: {data_path}")
            raise ValueError(f"Data file for '{symbol}' not found")
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            raise
    
    def get_commodity_data(
        self, 
        commodity: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical data for a specific symbol
        
        Args:
            commodity: Symbol code
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            List of data points
        """
        symbol_data = self.load_symbol_data(commodity)
        data_points = symbol_data.get('data', [])
        
        # Filter by date range if specified
        if start_date or end_date:
            filtered_data = []
            for point in data_points:
                point_date = point['date']
                if start_date and point_date < start_date:
                    continue
                if end_date and point_date > end_date:
                    continue
                filtered_data.append(point)
            return filtered_data
        
        return data_points
    
    def get_multiple_commodities(
        self,
        commodities: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical data for multiple symbols
        
        Args:
            commodities: List of symbol codes
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary mapping symbol to its data points
        """
        result = {}
        for commodity in commodities:
            result[commodity] = self.get_commodity_data(commodity, start_date, end_date)
        return result
    
    def get_date_range(self) -> Dict[str, str]:
        """Get the available date range across all symbols"""
        symbols = self.get_commodities()
        
        if not symbols:
            return {'start_date': None, 'end_date': None}
        
        all_dates = []
        for symbol in symbols:
            try:
                data = self.load_symbol_data(symbol)
                for point in data.get('data', []):
                    all_dates.append(point['date'])
            except Exception as e:
                logger.warning(f"Error loading data for {symbol}: {e}")
                continue
        
        if not all_dates:
            return {'start_date': None, 'end_date': None}
        
        return {
            'start_date': min(all_dates),
            'end_date': max(all_dates),
            'total_points': len(all_dates)
        }
    
    def get_commodity_info(self, commodity: str) -> Dict:
        """Get metadata about a symbol"""
        # Get from metadata first
        symbols = self.get_symbols()
        symbol_info = next((s for s in symbols if s['symbol'] == commodity), None)
        
        if not symbol_info:
            raise ValueError(f"Symbol '{commodity}' not found in metadata")
        
        # Load data to get date range
        try:
            data = self.load_symbol_data(commodity)
            data_points = data.get('data', [])
            dates = [point['date'] for point in data_points]
            
            return {
                'symbol': commodity,
                'name': symbol_info.get('name', commodity),
                'type': symbol_info.get('type', 'unknown'),
                'exchange': symbol_info.get('exchange'),
                'sector': symbol_info.get('sector'),
                'unit': symbol_info.get('unit'),
                'available_from': min(dates) if dates else None,
                'available_to': max(dates) if dates else None,
                'data_points': len(data_points)
            }
        except Exception as e:
            logger.error(f"Error getting info for {commodity}: {e}")
            raise
