"""
Flask API Server for Stock Technical Analysis
Serves stock data, technical indicators, and news sentiment to the frontend.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

from stock_fetcher import fetch_stock_data, get_stock_info
from technical_analysis import apply_all_indicators, analyze_signals, get_buy_sell_recommendations
from news_sentiment import fetch_stock_news, analyze_news_sentiment
from stock_search import search_stocks

app = Flask(__name__, static_folder='static')
CORS(app)


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """
    Get stock data with technical indicators.
    
    Query params:
        period: Data period (default: 6mo)
    """
    period = request.args.get('period', '6mo')
    
    try:
        # Fetch stock data
        df = fetch_stock_data(symbol.upper(), period=period)
        stock_info = get_stock_info(symbol.upper())
        
        # Apply technical indicators
        df = apply_all_indicators(df)
        
        # Analyze signals
        signals = analyze_signals(df)
        
        # Get buy/sell recommendations
        recommendations = get_buy_sell_recommendations(df)
        
        # Convert DataFrame to JSON-friendly format
        # Reset index to include Date as a column
        df_reset = df.reset_index()
        df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
        
        # Convert to dict and handle NaN values properly
        import json
        import math
        
        def clean_nan(obj):
            """Recursively replace NaN and Inf with None."""
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            return obj
        
        records = df_reset.to_dict(orient='records')
        clean_records = clean_nan(records)
        
        data = {
            'success': True,
            'symbol': symbol.upper(),
            'info': stock_info,
            'signals': clean_nan(signals),
            'recommendations': clean_nan(recommendations),
            'data': clean_records,
            'columns': list(df_reset.columns)
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/news/<symbol>')
def get_news(symbol):
    """Get news and sentiment analysis for a stock."""
    max_news = request.args.get('limit', 10, type=int)
    
    try:
        news = fetch_stock_news(symbol.upper(), max_news=max_news)
        sentiment_results = analyze_news_sentiment(news)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'sentiment': sentiment_results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/search')
def search():
    """Search for stock symbols by name or symbol."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': True, 'results': []})
    
    results = search_stocks(query, max_results=10)
    
    return jsonify({
        'success': True,
        'results': results
    })


if __name__ == '__main__':
    # Create static folder if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    print("\n🚀 Starting Stock Analysis Dashboard...")
    print("📊 Open http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000)
