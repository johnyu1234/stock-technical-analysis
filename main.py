"""
US Stock Market Technical Analysis Tool
Main application for fetching stock data and performing technical analysis.

Usage:
    python main.py [SYMBOL]
    
Example:
    python main.py TSLA
    python main.py AAPL
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from stock_fetcher import fetch_stock_data, get_stock_info
from technical_analysis import apply_all_indicators, analyze_signals
from news_sentiment import fetch_stock_news, analyze_news_sentiment, print_news_analysis


def create_chart(df, symbol: str, stock_info: dict):
    """
    Create a multi-panel chart with price, volume, and technical indicators.
    """
    # Set up the figure with subplots
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), 
                              gridspec_kw={'height_ratios': [3, 1, 1, 1]})
    fig.suptitle(f"{stock_info.get('name', symbol)} ({symbol}) - Technical Analysis", 
                 fontsize=14, fontweight='bold')
    
    # Color scheme
    colors = {
        'price': '#2E86AB',
        'sma_20': '#F18F01',
        'sma_50': '#C73E1D',
        'bb_upper': '#A23B72',
        'bb_lower': '#A23B72',
        'bb_fill': '#E8D5E0',
        'volume_up': '#26A65B',
        'volume_down': '#E74C3C',
        'macd': '#2E86AB',
        'macd_signal': '#F18F01',
        'macd_hist_pos': '#26A65B',
        'macd_hist_neg': '#E74C3C',
        'rsi': '#8E44AD',
        'rsi_overbought': '#E74C3C',
        'rsi_oversold': '#26A65B',
    }
    
    # ============ Panel 1: Price with Moving Averages and Bollinger Bands ============
    ax1 = axes[0]
    
    # Bollinger Bands fill
    ax1.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], 
                     alpha=0.2, color=colors['bb_fill'], label='Bollinger Bands')
    ax1.plot(df.index, df['BB_Upper'], color=colors['bb_upper'], 
             linewidth=0.8, linestyle='--', alpha=0.7)
    ax1.plot(df.index, df['BB_Lower'], color=colors['bb_lower'], 
             linewidth=0.8, linestyle='--', alpha=0.7)
    
    # Price line
    ax1.plot(df.index, df['Close'], color=colors['price'], 
             linewidth=1.5, label='Close Price')
    
    # Moving Averages
    ax1.plot(df.index, df['SMA_20'], color=colors['sma_20'], 
             linewidth=1.2, label='SMA 20', alpha=0.9)
    ax1.plot(df.index, df['SMA_50'], color=colors['sma_50'], 
             linewidth=1.2, label='SMA 50', alpha=0.9)
    
    ax1.set_ylabel('Price (USD)', fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(df.index[0], df.index[-1])
    
    # ============ Panel 2: Volume ============
    ax2 = axes[1]
    
    # Color volume bars based on price direction
    volume_colors = [colors['volume_up'] if df['Close'].iloc[i] >= df['Open'].iloc[i] 
                     else colors['volume_down'] for i in range(len(df))]
    ax2.bar(df.index, df['Volume'], color=volume_colors, alpha=0.7, width=0.8)
    ax2.set_ylabel('Volume', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(df.index[0], df.index[-1])
    
    # Format volume in millions
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    
    # ============ Panel 3: MACD ============
    ax3 = axes[2]
    
    ax3.plot(df.index, df['MACD'], color=colors['macd'], 
             linewidth=1.2, label='MACD')
    ax3.plot(df.index, df['MACD_Signal'], color=colors['macd_signal'], 
             linewidth=1.2, label='Signal')
    
    # Histogram
    hist_colors = [colors['macd_hist_pos'] if val >= 0 else colors['macd_hist_neg'] 
                   for val in df['MACD_Histogram']]
    ax3.bar(df.index, df['MACD_Histogram'], color=hist_colors, alpha=0.5, width=0.8)
    
    ax3.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax3.set_ylabel('MACD', fontweight='bold')
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(df.index[0], df.index[-1])
    
    # ============ Panel 4: RSI ============
    ax4 = axes[3]
    
    ax4.plot(df.index, df['RSI'], color=colors['rsi'], linewidth=1.2, label='RSI (14)')
    ax4.axhline(y=70, color=colors['rsi_overbought'], linestyle='--', 
                linewidth=1, label='Overbought (70)')
    ax4.axhline(y=30, color=colors['rsi_oversold'], linestyle='--', 
                linewidth=1, label='Oversold (30)')
    ax4.axhline(y=50, color='gray', linestyle='-', linewidth=0.5)
    
    ax4.fill_between(df.index, 70, 100, alpha=0.1, color=colors['rsi_overbought'])
    ax4.fill_between(df.index, 0, 30, alpha=0.1, color=colors['rsi_oversold'])
    
    ax4.set_ylabel('RSI', fontweight='bold')
    ax4.set_ylim(0, 100)
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(df.index[0], df.index[-1])
    ax4.set_xlabel('Date', fontweight='bold')
    
    # Format x-axis dates
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig


def print_analysis(symbol: str, stock_info: dict, signals: dict):
    """
    Print a summary of the technical analysis.
    """
    print("\n" + "=" * 60)
    print(f"  TECHNICAL ANALYSIS: {stock_info.get('name', symbol)} ({symbol})")
    print("=" * 60)
    
    print(f"\n  📊 Current Price: ${signals.get('price', 0):.2f}")
    print(f"  📅 Date: {signals.get('date', 'N/A')}")
    print(f"  🏢 Sector: {stock_info.get('sector', 'N/A')}")
    print(f"  🏭 Industry: {stock_info.get('industry', 'N/A')}")
    
    print("\n" + "-" * 60)
    print("  SIGNALS SUMMARY")
    print("-" * 60)
    
    # Trend
    trend = signals.get('trend', {})
    print(f"\n  📈 TREND: {trend.get('signal', 'N/A')}")
    print(f"     {trend.get('description', '')}")
    
    # RSI
    rsi = signals.get('rsi', {})
    rsi_emoji = "🔴" if rsi.get('signal') == 'OVERBOUGHT' else "🟢" if rsi.get('signal') == 'OVERSOLD' else "⚪"
    print(f"\n  {rsi_emoji} RSI ({rsi.get('value', 0):.1f}): {rsi.get('signal', 'N/A')}")
    print(f"     {rsi.get('description', '')}")
    
    # MACD
    macd = signals.get('macd', {})
    macd_emoji = "🟢" if 'BULLISH' in macd.get('signal', '') else "🔴"
    print(f"\n  {macd_emoji} MACD: {macd.get('signal', 'N/A')}")
    print(f"     {macd.get('description', '')}")
    
    # Bollinger Bands
    bb = signals.get('bollinger', {})
    bb_emoji = "🔴" if 'UPPER' in bb.get('signal', '') else "🟢" if 'LOWER' in bb.get('signal', '') else "⚪"
    print(f"\n  {bb_emoji} BOLLINGER: {bb.get('signal', 'N/A')}")
    print(f"     {bb.get('description', '')}")
    
    print("\n" + "=" * 60)
    print("  ⚠️  Disclaimer: This is for educational purposes only.")
    print("      Not financial advice. Do your own research.")
    print("=" * 60 + "\n")


def main():
    # Get symbol from command line or use default
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "TSLA"
    period = sys.argv[2] if len(sys.argv) > 2 else "6mo"
    
    print(f"\n🔍 Fetching data for {symbol}...")
    
    try:
        # Fetch stock data
        df = fetch_stock_data(symbol, period=period)
        stock_info = get_stock_info(symbol)
        
        print(f"✅ Retrieved {len(df)} data points")
        
        # Apply technical indicators
        print("📊 Calculating technical indicators...")
        df = apply_all_indicators(df)
        
        # Analyze signals
        signals = analyze_signals(df)
        
        # Print technical analysis
        print_analysis(symbol, stock_info, signals)
        
        # Fetch and analyze news sentiment
        print("\n📰 Fetching latest news...")
        news = fetch_stock_news(symbol, max_news=10)
        print(f"✅ Found {len(news)} news articles")
        
        sentiment_results = analyze_news_sentiment(news)
        print_news_analysis(symbol, sentiment_results)
        
        # Create and show chart
        print("📈 Generating chart...")
        fig = create_chart(df, symbol, stock_info)
        plt.show()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
