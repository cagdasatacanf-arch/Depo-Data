# Depo - Historical Stock & Metal Data System

> **Phase 1: Closed System** - Working with existing historical data

A modern backend system for visualizing and analyzing historical commodity and stock prices, designed to integrate with a Lovable frontend.

## 🎯 Overview

Depo provides a FastAPI backend that serves historical price data for various commodities (metals, agricultural products, energy) and stocks. The system works with pre-loaded CSV data and provides RESTful endpoints for data retrieval, statistical analysis, and multi-asset comparison.

## ✨ Features

- 📊 **Historical Data Access** - Query years of commodity price data
- 🔍 **Multi-Asset Comparison** - Compare trends across different commodities
- 📈 **Statistical Analysis** - Calculate volatility, returns, correlations
- 🎯 **Date Range Filtering** - Flexible time-based querying
- 🚀 **Fast API** - High-performance REST endpoints
- 📚 **Auto Documentation** - Interactive Swagger UI
- 🌐 **CORS Enabled** - Ready for frontend integration

## 📁 Project Structure

```
depo/
├── api/                    # API routes and models
│   ├── routes.py          # REST endpoints
│   └── models.py          # Pydantic schemas
├── data/                   # Data processing layer
│   ├── loader.py          # CSV data loader
│   └── processor.py       # Data transformation utilities
├── Database/              # Your existing data files
│   └── data/
│       └── commodity_prices.csv
├── config/                # Configuration files
├── docs/                  # Documentation
├── tests/                 # Test suites
├── main.py               # FastAPI application entry
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-github-repo-url>
   cd depo
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

## 📡 API Endpoints

### Get All Commodities
```
GET /api/commodities
```
Returns list of all available commodities.

### Get Historical Data
```
GET /api/commodities/{commodity_name}/history?start_year=1960&end_year=2021
```
Returns historical price data for a specific commodity.

**Parameters:**
- `commodity_name` - Name of the commodity (e.g., "Gold", "Crude Oil")
- `start_year` - Optional start year (default: earliest available)
- `end_year` - Optional end year (default: latest available)

### Compare Commodities
```
GET /api/commodities/compare?names=Gold,Silver,Platinum
```
Compare price trends across multiple commodities.

### Get Statistics
```
GET /api/stats/{commodity_name}
```
Get statistical summary (mean, std, min, max, volatility) for a commodity.

### Get Date Range
```
GET /api/date-range
```
Get the available date range in the dataset.

## 💻 Example Usage

### Python
```python
import requests

# Get all commodities
response = requests.get('http://localhost:8000/api/commodities')
commodities = response.json()

# Get gold price history
response = requests.get('http://localhost:8000/api/commodities/Gold/history')
gold_data = response.json()

# Compare metals
response = requests.get('http://localhost:8000/api/commodities/compare?names=Gold,Silver,Platinum')
comparison = response.json()
```

### JavaScript (for Lovable frontend)
```javascript
// Fetch commodities list
const response = await fetch('http://localhost:8000/api/commodities');
const commodities = await response.json();

// Get historical data
const goldData = await fetch('http://localhost:8000/api/commodities/Gold/history?start_year=2000');
const history = await goldData.json();
```

## 📊 Data Sources

Current dataset includes historical prices (1960-2021) for:

**Metals**: Gold, Platinum, Silver

**Energy**: Crude Oil, Coal, Natural Gas

**Agriculture**: Cocoa, Coffee, Tea, Sugar, Cotton, Rice, Wheat, Corn, etc.

**Oils**: Coconut Oil, Palm Oil, Soybean Oil, Groundnut Oil

**Livestock**: Beef, Chicken, Lamb, Shrimps

**Other**: Timber (Logs, Sawnwood)

## 🔧 Development

### Run Tests
```bash
pytest tests/
```

### Code Style
```bash
# Install dev dependencies
pip install black flake8

# Format code
black .

# Lint
flake8 .
```

## 🌍 Deployment

### Local Development
Already covered in Quick Start above.

### Production (Example with Docker - Coming Soon)
```bash
docker build -t depo-api .
docker run -p 8000:8000 depo-api
```

## 🛣️ Roadmap

### Phase 1: Closed System ✅ (Current)
- [x] Project structure setup
- [ ] FastAPI backend implementation
- [ ] CSV data loader
- [ ] REST API endpoints
- [ ] Statistical calculations
- [ ] Documentation

### Phase 2: External Data Integration (Future)
- [ ] Yahoo Finance integration
- [ ] Alpha Vantage integration
- [ ] Automated data updates
- [ ] Real-time price feeds
- [ ] Database persistence

### Phase 3: Advanced Features (Future)
- [ ] Machine learning predictions
- [ ] Pattern detection algorithms
- [ ] Alert system
- [ ] User authentication
- [ ] Data export functionality

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

ISC License

## 👨‍💻 Author

Created with ❤️ for historical data analysis

## 🔗 Links

- Frontend (Lovable): [Coming Soon]
- API Documentation: http://localhost:8000/docs (when running)
- GitHub Issues: [Your repo]/issues

---

**Note**: This is Phase 1 focusing on existing data. External API integration for fetching new data will be added in Phase 2.
