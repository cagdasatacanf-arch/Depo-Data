"""
Pydantic models for API request/response validation
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class CommodityInfo(BaseModel):
    """Commodity metadata"""
    name: str = Field(..., description="Commodity name")
    category: Optional[str] = Field(None, description="Category (Metals, Energy, Agriculture, etc.)")
    unit: Optional[str] = Field(None, description="Price unit ($/oz, $/barrel, etc.)")
    available_from: Optional[int] = Field(None, description="First year of data")
    available_to: Optional[int] = Field(None, description="Last year of data")


class PriceDataPoint(BaseModel):
    """Single price data point"""
    year: int = Field(..., description="Year")
    price: float = Field(..., description="Price in USD")


class PriceHistory(BaseModel):
    """Historical price data response"""
    commodity: str = Field(..., description="Commodity name")
    data: List[PriceDataPoint] = Field(..., description="Historical price data")
    count: int = Field(..., description="Number of data points")


class ComparisonData(BaseModel):
    """Multi-commodity comparison response"""
    commodities: List[str] = Field(..., description="List of commodity names")
    years: List[int] = Field(..., description="Years in dataset")
    data: Dict[str, List[Optional[float]]] = Field(..., description="Price data by commodity")


class Statistics(BaseModel):
    """Statistical summary for a commodity"""
    commodity: str = Field(..., description="Commodity name")
    mean: float = Field(..., description="Average price")
    median: float = Field(..., description="Median price")
    std_dev: float = Field(..., description="Standard deviation")
    min_price: float = Field(..., description="Minimum price")
    max_price: float = Field(..., description="Maximum price")
    min_year: int = Field(..., description="Year of minimum price")
    max_year: int = Field(..., description="Year of maximum price")
    total_change_pct: float = Field(..., description="Total percentage change from start to end")
    volatility: float = Field(..., description="Price volatility (coefficient of variation)")


class DateRangeResponse(BaseModel):
    """Available date range in dataset"""
    start_year: int = Field(..., description="First year in dataset")
    end_year: int = Field(..., description="Last year in dataset")
    total_years: int = Field(..., description="Total number of years")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server time")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
