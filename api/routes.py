"""
API Routes for commodity price data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from api.models import (
    CommodityInfo,
    PriceHistory,
    PriceDataPoint,
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
router = APIRouter(prefix="/api", tags=["commodities"])

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


@router.get("/commodities", response_model=List[str])
async def get_commodities():
    """
    Get list of all available commodities
    
    Returns:
        List of commodity names
    """
    try:
        commodities = data_loader.get_commodities()
        return commodities
    except Exception as e:
        logger.error(f"Error fetching commodities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/{commodity_name}/info", response_model=CommodityInfo)
async def get_commodity_info(commodity_name: str):
    """
    Get metadata about a specific commodity
    
    Args:
        commodity_name: Name of the commodity
        
    Returns:
        Commodity metadata
    """
    try:
        info = data_loader.get_commodity_info(commodity_name)
        return CommodityInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching commodity info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/{commodity_name}/history", response_model=PriceHistory)
async def get_commodity_history(
    commodity_name: str,
    start_year: Optional[int] = Query(None, description="Start year (inclusive)"),
    end_year: Optional[int] = Query(None, description="End year (inclusive)")
):
    """
    Get historical price data for a commodity
    
    Args:
        commodity_name: Name of the commodity
        start_year: Optional start year filter
        end_year: Optional end year filter
        
    Returns:
        Historical price data
    """
    try:
        df = data_loader.get_commodity_data(commodity_name, start_year, end_year)
        
        # Convert to response format
        data_points = [
            PriceDataPoint(year=int(row['Year']), price=float(row['price']))
            for _, row in df.iterrows()
        ]
        
        return PriceHistory(
            commodity=commodity_name,
            data=data_points,
            count=len(data_points)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching commodity history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/compare", response_model=ComparisonData)
async def compare_commodities(
    names: str = Query(..., description="Comma-separated list of commodity names"),
    start_year: Optional[int] = Query(None, description="Start year (inclusive)"),
    end_year: Optional[int] = Query(None, description="End year (inclusive)")
):
    """
    Compare historical data for multiple commodities
    
    Args:
        names: Comma-separated commodity names
        start_year: Optional start year filter
        end_year: Optional end year filter
        
    Returns:
        Comparison data for multiple commodities
    """
    try:
        # Parse commodity names
        commodity_list = [name.strip() for name in names.split(',')]
        
        if len(commodity_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least 2 commodities to compare"
            )
        
        # Get data for all commodities
        df = data_loader.get_multiple_commodities(commodity_list, start_year, end_year)
        
        # Prepare response data
        years = df['Year'].tolist()
        data_dict = {}
        
        for commodity in commodity_list:
            # Convert NaN to None for JSON serialization
            prices = df[commodity].replace({float('nan'): None}).tolist()
            data_dict[commodity] = prices
        
        return ComparisonData(
            commodities=commodity_list,
            years=years,
            data=data_dict
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing commodities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{commodity_name}", response_model=Statistics)
async def get_commodity_statistics(
    commodity_name: str,
    start_year: Optional[int] = Query(None, description="Start year (inclusive)"),
    end_year: Optional[int] = Query(None, description="End year (inclusive)")
):
    """
    Get statistical summary for a commodity
    
    Args:
        commodity_name: Name of the commodity
        start_year: Optional start year filter
        end_year: Optional end year filter
        
    Returns:
        Statistical summary
    """
    try:
        df = data_loader.get_commodity_data(commodity_name, start_year, end_year)
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {commodity_name}"
            )
        
        stats = processor.calculate_statistics(df, commodity_name)
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
        Available start and end years
    """
    try:
        date_info = data_loader.get_date_range()
        return DateRangeResponse(**date_info)
    except Exception as e:
        logger.error(f"Error fetching date range: {e}")
        raise HTTPException(status_code=500, detail=str(e))
