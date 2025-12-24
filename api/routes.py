"""
API Routes for stock and metal price data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from api.models import (
    SymbolInfo,
    CommodityInfo,
    PriceHistory,
    OHLCVDataPoint,
    ComparisonData,
    Statistics,
    DateRangeResponse,
    HealthResponse,
    ErrorResponse
)
from data.loader import DataLoader
from data.processor import DataProcessor

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api", tags=["stocks_and_metals"])

# Initialize data loader (singleton pattern)
data_loader = DataLoader()
processor = DataProcessor()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }


@router.get("/symbols", response_model=List[SymbolInfo])
async def get_symbols():
    """
    Get list of all available symbols with metadata
    
    Returns:
        List of symbol information
    """
    try:
        symbols = data_loader.get_symbols()
        return symbols
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities", response_model=List[str])
async def get_commodities():
    """
    Get list of all available symbol codes (legacy endpoint)
    
    Returns:
        List of symbol codes
    """
    try:
        commodities = data_loader.get_commodities()
        return commodities
    except Exception as e:
        logger.error(f"Error fetching commodities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/{symbol}/info", response_model=CommodityInfo)
async def get_commodity_info(symbol: str):
    """
    Get metadata about a specific symbol
    
    Args:
        symbol: Symbol code (e.g., AAPL, XAU)
        
    Returns:
        Symbol metadata
    """
    try:
        info = data_loader.get_commodity_info(symbol)
        return CommodityInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching symbol info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/{symbol}/history", response_model=PriceHistory)
async def get_commodity_history(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get historical OHLCV data for a symbol
    
    Args:
        symbol: Symbol code
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Historical OHLCV data
    """
    try:
        # Get symbol metadata
        symbol_data = data_loader.load_symbol_data(symbol)
        
        # Get historical data points
        data_points = data_loader.get_commodity_data(symbol, start_date, end_date)
        
        # Convert to OHLCVDataPoint models
        ohlcv_points = [OHLCVDataPoint(**point) for point in data_points]
        
        return PriceHistory(
            symbol=symbol,
            name=symbol_data.get('name', symbol),
            type=symbol_data.get('type', 'unknown'),
            data=ohlcv_points,
            count=len(ohlcv_points)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching symbol history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/compare", response_model=ComparisonData)
async def compare_commodities(
    symbols: str = Query(..., description="Comma-separated list of symbol codes"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Compare historical data for multiple symbols
    
    Args:
        symbols: Comma-separated symbol codes
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Comparison data for multiple symbols
    """
    try:
        # Parse symbol codes
        symbol_list = [s.strip() for s in symbols.split(',')]
        
        if len(symbol_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least 2 symbols to compare"
            )
        
        # Get data for all symbols
        all_data = data_loader.get_multiple_commodities(symbol_list, start_date, end_date)
        
        # Convert to OHLCVDataPoint models
        formatted_data = {}
        for symbol, data_points in all_data.items():
            formatted_data[symbol] = [OHLCVDataPoint(**point) for point in data_points]
        
        return ComparisonData(
            symbols=symbol_list,
            data=formatted_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{symbol}", response_model=Statistics)
async def get_commodity_statistics(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get statistical summary for a symbol
    
    Args:
        symbol: Symbol code
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Statistical summary
    """
    try:
        data_points = data_loader.get_commodity_data(symbol, start_date, end_date)
        
        if not data_points:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {symbol}"
            )
        
        stats = processor.calculate_statistics(data_points, symbol)
        return Statistics(**stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/date-range", response_model=DateRangeResponse)
async def get_date_range():
    """
    Get the available date range in the dataset
    
    Returns:
        Available start and end dates
    """
    try:
        date_info = data_loader.get_date_range()
        return DateRangeResponse(**date_info)
    except Exception as e:
        logger.error(f"Error fetching date range: {e}")
        raise HTTPException(status_code=500, detail=str(e))

