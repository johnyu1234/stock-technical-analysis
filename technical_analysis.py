"""
Technical Analysis Module
Calculates various technical indicators for stock analysis.
"""

import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Simple Moving Averages (SMA) and Exponential Moving Averages (EMA).
    
    Adds:
        - SMA_20: 20-period Simple Moving Average
        - SMA_50: 50-period Simple Moving Average
        - EMA_12: 12-period Exponential Moving Average
        - EMA_26: 26-period Exponential Moving Average
    """
    df = df.copy()
    
    # Simple Moving Averages
    df['SMA_20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    df['SMA_50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
    
    # Exponential Moving Averages
    df['EMA_12'] = EMAIndicator(close=df['Close'], window=12).ema_indicator()
    df['EMA_26'] = EMAIndicator(close=df['Close'], window=26).ema_indicator()
    
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add MACD (Moving Average Convergence Divergence) indicators.
    
    Adds:
        - MACD: MACD line (12-period EMA - 26-period EMA)
        - MACD_Signal: 9-period EMA of MACD
        - MACD_Histogram: MACD - Signal line
    """
    df = df.copy()
    
    macd = MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Histogram'] = macd.macd_diff()
    
    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Add RSI (Relative Strength Index).
    
    Args:
        df: DataFrame with 'Close' column
        window: RSI period (default 14)
    
    Adds:
        - RSI: Relative Strength Index (0-100 scale)
    """
    df = df.copy()
    df['RSI'] = RSIIndicator(close=df['Close'], window=window).rsi()
    return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    Add Bollinger Bands.
    
    Args:
        df: DataFrame with 'Close' column
        window: Moving average period (default 20)
        std_dev: Number of standard deviations (default 2.0)
    
    Adds:
        - BB_Upper: Upper Bollinger Band
        - BB_Middle: Middle Band (SMA)
        - BB_Lower: Lower Bollinger Band
        - BB_Width: Band width percentage
    """
    df = df.copy()
    
    bb = BollingerBands(close=df['Close'], window=window, window_dev=std_dev)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Middle'] = bb.bollinger_mavg()
    df['BB_Lower'] = bb.bollinger_lband()
    df['BB_Width'] = bb.bollinger_wband()
    
    return df


def apply_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all technical indicators to the dataframe.
    """
    df = add_moving_averages(df)
    df = add_macd(df)
    df = add_rsi(df)
    df = add_bollinger_bands(df)
    return df


def analyze_signals(df: pd.DataFrame) -> dict:
    """
    Analyze the latest data point and generate trading signals.
    
    Returns:
        Dictionary with signal analysis
    """
    if df.empty:
        return {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    signals = {
        'price': latest['Close'],
        'date': df.index[-1].strftime('%Y-%m-%d') if hasattr(df.index[-1], 'strftime') else str(df.index[-1]),
    }
    
    # RSI Analysis
    rsi = latest.get('RSI', 50)
    if rsi > 70:
        signals['rsi'] = {'value': rsi, 'signal': 'OVERBOUGHT', 'description': 'RSI above 70 - potential reversal down'}
    elif rsi < 30:
        signals['rsi'] = {'value': rsi, 'signal': 'OVERSOLD', 'description': 'RSI below 30 - potential reversal up'}
    else:
        signals['rsi'] = {'value': rsi, 'signal': 'NEUTRAL', 'description': 'RSI in normal range'}
    
    # MACD Analysis
    macd = latest.get('MACD', 0)
    macd_signal = latest.get('MACD_Signal', 0)
    prev_macd = prev.get('MACD', 0)
    prev_signal = prev.get('MACD_Signal', 0)
    
    if prev_macd < prev_signal and macd > macd_signal:
        signals['macd'] = {'value': macd, 'signal': 'BULLISH CROSSOVER', 'description': 'MACD crossed above signal line'}
    elif prev_macd > prev_signal and macd < macd_signal:
        signals['macd'] = {'value': macd, 'signal': 'BEARISH CROSSOVER', 'description': 'MACD crossed below signal line'}
    elif macd > macd_signal:
        signals['macd'] = {'value': macd, 'signal': 'BULLISH', 'description': 'MACD above signal line'}
    else:
        signals['macd'] = {'value': macd, 'signal': 'BEARISH', 'description': 'MACD below signal line'}
    
    # Moving Average Analysis
    sma_20 = latest.get('SMA_20', 0)
    sma_50 = latest.get('SMA_50', 0)
    close = latest['Close']
    
    if close > sma_20 > sma_50:
        signals['trend'] = {'signal': 'STRONG UPTREND', 'description': 'Price > SMA20 > SMA50'}
    elif close > sma_20:
        signals['trend'] = {'signal': 'UPTREND', 'description': 'Price above SMA20'}
    elif close < sma_20 < sma_50:
        signals['trend'] = {'signal': 'STRONG DOWNTREND', 'description': 'Price < SMA20 < SMA50'}
    elif close < sma_20:
        signals['trend'] = {'signal': 'DOWNTREND', 'description': 'Price below SMA20'}
    else:
        signals['trend'] = {'signal': 'NEUTRAL', 'description': 'No clear trend'}
    
    # Bollinger Bands Analysis
    bb_upper = latest.get('BB_Upper', 0)
    bb_lower = latest.get('BB_Lower', 0)
    
    if close >= bb_upper:
        signals['bollinger'] = {'signal': 'AT UPPER BAND', 'description': 'Price at/above upper band - potential resistance'}
    elif close <= bb_lower:
        signals['bollinger'] = {'signal': 'AT LOWER BAND', 'description': 'Price at/below lower band - potential support'}
    else:
        signals['bollinger'] = {'signal': 'WITHIN BANDS', 'description': 'Price within normal range'}
    
    return signals


def get_buy_sell_recommendations(df: pd.DataFrame) -> dict:
    """
    Generate buy/sell recommendations for different timeframes based on technical analysis.
    
    Returns:
        Dictionary with recommendations for today, week, month, and year
    """
    if df.empty or len(df) < 50:
        return {}
    
    latest = df.iloc[-1]
    
    # Calculate scores for different indicators (-1 to 1 scale)
    scores = {}
    
    # RSI Score
    rsi = latest.get('RSI', 50)
    if rsi > 70:
        scores['rsi'] = -0.8  # Overbought - sell signal
    elif rsi > 60:
        scores['rsi'] = -0.4
    elif rsi < 30:
        scores['rsi'] = 0.8  # Oversold - buy signal
    elif rsi < 40:
        scores['rsi'] = 0.4
    else:
        scores['rsi'] = 0
    
    # MACD Score
    macd = latest.get('MACD', 0)
    macd_signal = latest.get('MACD_Signal', 0)
    macd_hist = latest.get('MACD_Histogram', 0)
    
    if macd > macd_signal and macd_hist > 0:
        scores['macd'] = 0.7  # Bullish
    elif macd < macd_signal and macd_hist < 0:
        scores['macd'] = -0.7  # Bearish
    else:
        scores['macd'] = 0
    
    # Moving Average Score
    close = latest['Close']
    sma_20 = latest.get('SMA_20', close)
    sma_50 = latest.get('SMA_50', close)
    
    if close > sma_20 > sma_50:
        scores['ma'] = 0.8  # Strong uptrend
    elif close > sma_20:
        scores['ma'] = 0.5
    elif close < sma_20 < sma_50:
        scores['ma'] = -0.8  # Strong downtrend
    elif close < sma_20:
        scores['ma'] = -0.5
    else:
        scores['ma'] = 0
    
    # Bollinger Bands Score
    bb_upper = latest.get('BB_Upper', close)
    bb_lower = latest.get('BB_Lower', close)
    bb_middle = latest.get('BB_Middle', close)
    
    if close >= bb_upper:
        scores['bb'] = -0.6  # At resistance
    elif close <= bb_lower:
        scores['bb'] = 0.6  # At support
    elif close > bb_middle:
        scores['bb'] = 0.3
    elif close < bb_middle:
        scores['bb'] = -0.3
    else:
        scores['bb'] = 0
    
    # Calculate weighted average score
    total_score = (
        scores['rsi'] * 0.25 +
        scores['macd'] * 0.30 +
        scores['ma'] * 0.30 +
        scores['bb'] * 0.15
    )
    
    # Generate recommendations for different timeframes
    def get_recommendation(score, timeframe_weight=1.0):
        adjusted_score = score * timeframe_weight
        
        if adjusted_score >= 0.5:
            return {'action': 'STRONG BUY', 'confidence': min(abs(adjusted_score) * 100, 100), 'color': 'success'}
        elif adjusted_score >= 0.2:
            return {'action': 'BUY', 'confidence': min(abs(adjusted_score) * 100, 100), 'color': 'success'}
        elif adjusted_score <= -0.5:
            return {'action': 'STRONG SELL', 'confidence': min(abs(adjusted_score) * 100, 100), 'color': 'danger'}
        elif adjusted_score <= -0.2:
            return {'action': 'SELL', 'confidence': min(abs(adjusted_score) * 100, 100), 'color': 'danger'}
        else:
            return {'action': 'HOLD', 'confidence': 50, 'color': 'warning'}
    
    # Different timeframes with different weights
    recommendations = {
        'today': get_recommendation(total_score, 1.0),  # Short-term - full weight
        'week': get_recommendation(total_score, 0.9),   # Slightly less aggressive
        'month': get_recommendation(total_score, 0.8),  # Medium-term
        'year': get_recommendation(total_score, 0.6),   # Long-term - more conservative
    }
    
    # Add overall score
    recommendations['overall_score'] = total_score
    recommendations['indicator_scores'] = scores
    
    return recommendations


if __name__ == "__main__":
    # Test with sample data
    from stock_fetcher import fetch_stock_data
    
    print("Testing technical analysis module...")
    df = fetch_stock_data("TSLA", period="3mo")
    df = apply_all_indicators(df)
    
    print(f"\nDataFrame columns: {list(df.columns)}")
    print(f"\nLast row with indicators:\n{df.iloc[-1]}")
    
    signals = analyze_signals(df)
    print("\nSignal Analysis:")
    for key, value in signals.items():
        print(f"  {key}: {value}")
