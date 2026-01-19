"""
Stock Data Fetcher Module
Fetches US stock market data using Yahoo Finance API.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime


def fetch_stock_data(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch stock OHLCV data from Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'TSLA', 'AAPL')
        period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: Data interval - 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    
    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume, Adj Close
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            raise ValueError(f"No data found for symbol: {symbol}")
        
        # Clean up the dataframe
        df.index.name = 'Date'
        df = df.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')
        
        return df
    
    except Exception as e:
        raise Exception(f"Error fetching data for {symbol}: {str(e)}")


def get_stock_info(symbol: str) -> dict:
    """
    Get basic information about a stock.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dictionary with stock information
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'currency': info.get('currency', 'USD'),
            'exchange': info.get('exchange', 'N/A'),
        }
    except Exception:
        return {'name': symbol, 'sector': 'N/A', 'industry': 'N/A'}


if __name__ == "__main__":
    # Test the module
    print("Fetching TSLA data...")
    df = fetch_stock_data("TSLA", period="1mo")
    print(f"\nData shape: {df.shape}")
    print(f"\nLast 5 rows:\n{df.tail()}")
    
    print("\nStock Info:")
    info = get_stock_info("TSLA")
    for key, value in info.items():
        print(f"  {key}: {value}")
