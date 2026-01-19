"""
Stock Symbol Search Module
Provides autocomplete functionality using Yahoo Finance search API.
"""

import requests


def search_stocks(query: str, max_results: int = 10) -> list:
    """
    Search for stocks by symbol or company name using Yahoo Finance search API.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
    
    Returns:
        List of matching stocks with symbol, name, and exchange
    """
    if not query or len(query) < 1:
        return []
    
    try:
        # Use Yahoo Finance search API
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': max_results,
            'newsCount': 0,
            'enableFuzzyQuery': False,
            'quotesQueryId': 'tss_match_phrase_query'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        quotes = data.get('quotes', [])
        
        results = []
        for quote in quotes[:max_results]:
            # Filter for stocks (equities)
            quote_type = quote.get('quoteType', '')
            if quote_type in ['EQUITY', 'ETF', 'MUTUALFUND', 'INDEX']:
                results.append({
                    'symbol': quote.get('symbol', ''),
                    'name': quote.get('longname', quote.get('shortname', '')),
                    'exchange': quote.get('exchDisp', quote.get('exchange', '')),
                    'type': quote_type
                })
        
        return results
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        # Return empty list on error
        return []
