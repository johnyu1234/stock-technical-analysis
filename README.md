# Stock Technical Analysis Dashboard

A comprehensive Python-based stock market technical analysis tool with an interactive web dashboard featuring real-time data, advanced charting, and AI-powered buy/sell recommendations.

## Features

- 📊 **Interactive Charts**: Price (Line/Candlestick), Volume, MACD, RSI
- 🎯 **Multi-Timeframe Recommendations**: Buy/Sell signals for Today, Week, Month, Year
- 🔍 **Smart Stock Search**: Autocomplete with Yahoo Finance API
- 📰 **News Sentiment Analysis**: VADER sentiment on latest headlines
- 🖱️ **Advanced Tooltips**: Hover for OHLCV and indicator details
- 🎨 **Modern UI**: Dark theme with glassmorphism effects

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data (first time only)
python -c "import nltk; nltk.download('vader_lexicon')"
```

### Run the Dashboard

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## Project Structure

### Backend (Python)
- `stock_fetcher.py` - Fetches OHLCV data via yfinance
- `technical_analysis.py` - Calculates indicators + buy/sell recommendations
- `news_sentiment.py` - News headlines + VADER sentiment
- `stock_search.py` - Yahoo Finance search API
- `app.py` - Flask REST API server

### Frontend (HTML/CSS/JS)
- `static/index.html` - Dashboard structure
- `static/styles.css` - Dark theme styling
- `static/app.js` - Chart.js charts + interactions

## API Endpoints

- `GET /api/stock/{symbol}?period={period}` - Stock data with technical indicators
- `GET /api/news/{symbol}` - News articles with sentiment analysis
- `GET /api/search?q={query}` - Search for stock symbols

## Technologies

- **Backend**: Flask, yfinance, pandas, ta, NLTK VADER
- **Frontend**: Chart.js, chartjs-chart-financial, Luxon
- **Data Source**: Yahoo Finance API

## Buy/Sell Algorithm

The recommendation system uses a weighted scoring approach:
- RSI: 25%
- MACD: 30%
- Moving Averages: 30%
- Bollinger Bands: 15%

Timeframe adjustments:
- Today: 1.0x (most aggressive)
- This Week: 0.9x
- This Month: 0.8x
- This Year: 0.6x (most conservative)

## Screenshots

![Dashboard Preview](docs/dashboard.png)

## License

MIT License - feel free to use for personal or commercial projects.

## Author

Built with ❤️ using Python and Chart.js
