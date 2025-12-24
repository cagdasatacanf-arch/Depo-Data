"""
Pydantic models for API request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SymbolInfo(BaseModel):
    """Symbol metadata from metadata.json"""
    id: str = Field(..., description="Symbol ID")
    symbol: str = Field(..., description="Symbol code (e.g., AAPL, XAU)")
    name: str = Field(..., description="Full name")
    type: str = Field(..., description="Type (stock, metal, etc.)")
    exchange: Optional[str] = Field(None, description="Exchange (for stocks)")
    path: str = Field(..., description="Path to data file")
    sector: Optional[str] = Field(None, description="Sector (for stocks)")
    unit: Optional[str] = Field(None, description="Unit (for metals)")


class CommodityInfo(BaseModel):
    """Commodity/Symbol detailed information"""
    symbol: str = Field(..., description="Symbol code")
    name: str = Field(..., description="Full name")
    type: str = Field(..., description="Type (stock, metal, etc.)")
    exchange: Optional[str] = Field(None, description="Exchange")
    sector: Optional[str] = Field(None, description="Sector")
    unit: Optional[str] = Field(None, description="Unit")
    available_from: Optional[str] = Field(None, description="First date of data")
    available_to: Optional[str] = Field(None, description="Last date of data")
    data_points: int = Field(..., description="Number of data points")


class OHLCVDataPoint(BaseModel):
    """OHLCV data point with optional fields for stocks vs metals"""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: Optional[int] = Field(None, description="Volume (for stocks)")
    adjusted_close: Optional[float] = Field(None, description="Adjusted close (for stocks)")
    bid_ask_spread: Optional[float] = Field(None, description="Bid-ask spread (for metals)")


class PriceHistory(BaseModel):
    """Historical price data response"""
    symbol: str = Field(..., description="Symbol code")
    name: str = Field(..., description="Full name")
    type: str = Field(..., description="Type (stock, metal)")
    data: List[OHLCVDataPoint] = Field(..., description="Historical OHLCV data")
    count: int = Field(..., description="Number of data points")


class ComparisonData(BaseModel):
    """Multi-symbol comparison response"""
    symbols: List[str] = Field(..., description="List of symbol codes")
    data: Dict[str, List[OHLCVDataPoint]] = Field(..., description="Data by symbol")


class Statistics(BaseModel):
    """Statistical summary for a symbol"""
    symbol: str = Field(..., description="Symbol code")
    mean_close: float = Field(..., description="Average closing price")
    median_close: float = Field(..., description="Median closing price")
    std_dev: float = Field(..., description="Standard deviation")
    min_price: float = Field(..., description="Minimum closing price")
    max_price: float = Field(..., description="Maximum closing price")
    min_date: str = Field(..., description="Date of minimum price")
    max_date: str = Field(..., description="Date of maximum price")
    total_change_pct: float = Field(..., description="Total percentage change")
    volatility: float = Field(..., description="Price volatility")


class DateRangeResponse(BaseModel):
    """Available date range in dataset"""
    start_date: Optional[str] = Field(None, description="First date in dataset")
    end_date: Optional[str] = Field(None, description="Last date in dataset")
    total_points: Optional[int] = Field(None, description="Total data points")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server time")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

