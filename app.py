"""
Flask API Server for Stock Technical Analysis
Serves stock data, technical indicators, and news sentiment to the frontend.
With MySQL audit logging for request/response tracking.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import logging

from stock_fetcher import fetch_stock_data, get_stock_info
from technical_analysis import apply_all_indicators, analyze_signals, get_buy_sell_recommendations
from news_sentiment import fetch_stock_news, analyze_news_sentiment
from stock_search import search_stocks

# Audit logging imports
try:
    from database import init_connection_pool, audit_log, close_pool, health_check
    AUDIT_ENABLED = True
except ImportError:
    AUDIT_ENABLED = False
    logging.warning("Database module not available. Audit logging disabled.")
    # Create a no-op decorator when audit is disabled
    def audit_log(func):
        return func

app = Flask(__name__, static_folder='static')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/stock/<symbol>')
@audit_log
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
@audit_log
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
@audit_log
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


@app.route('/api/news/market/<region>')
@audit_log
def get_market_news(region):
    """
    Get news and sentiment analysis for a specific market region.
    Regions: US, HK, CHINA, TAIWAN
    """
    region = region.upper()
    max_news = request.args.get('limit', 10, type=int)
    
    # Map regions to major index symbols
    region_map = {
        'US': '^GSPC',        # S&P 500
        'HK': '^HSI',         # Hang Seng Index
        'CHINA': '000001.SS',  # SSE Composite
        'TAIWAN': '^TWII'     # TSEC Weighted
    }
    
    symbol = region_map.get(region)
    if not symbol:
        return jsonify({
            'success': False,
            'error': f'Invalid region: {region}. Supported regions: US, HK, CHINA, TAIWAN'
        }), 400
    
    try:
        news = fetch_stock_news(symbol, max_news=max_news)
        sentiment_results = analyze_news_sentiment(news)
        
        return jsonify({
            'success': True,
            'region': region,
            'symbol': symbol,
            'sentiment': sentiment_results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/health')
def health():
    """Health check endpoint for monitoring."""
    db_healthy = False
    if AUDIT_ENABLED:
        try:
            db_healthy = health_check()
        except Exception:
            db_healthy = False
    
    return jsonify({
        'status': 'healthy',
        'audit_logging': AUDIT_ENABLED,
        'database_connected': db_healthy
    })


if __name__ == '__main__':
    # Create static folder if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Initialize database connection pool for audit logging
    if AUDIT_ENABLED:
        try:
            init_connection_pool()
            logger.info("✅ Audit logging database initialized")
        except Exception as e:
            logger.warning(f"⚠️ Audit logging disabled: {e}")
    
    print("\n🚀 Starting Stock Analysis Dashboard...")
    print("📊 Open http://localhost:5000 in your browser")
    if AUDIT_ENABLED:
        print("📝 Audit logging: ENABLED")
    else:
        print("📝 Audit logging: DISABLED")
    print("Press Ctrl+C to stop\n")
    
    try:
        app.run(debug=True, port=5000)
    finally:
        if AUDIT_ENABLED:
            close_pool()

