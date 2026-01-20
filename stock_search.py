"""
Stock Symbol Search Module
Provides autocomplete functionality using Yahoo Finance search API.
With audit logging for external API calls.
"""

import requests
import time

# Import audit logging (graceful fallback if not available)
try:
    from database.audit_logger import get_audit_logger
    AUDIT_ENABLED = True
except ImportError:
    AUDIT_ENABLED = False


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
    
    start_time = time.time()
    status = 'SUCCESS'
    error_message = None
    response_status = 200
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        response_status = response.status_code
        
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
        status = 'ERROR'
        error_message = str(e)
        response_status = 500
        print(f"Search error: {str(e)}")
        return []
    
    finally:
        # Log external API call
        if AUDIT_ENABLED:
            try:
                execution_time_ms = int((time.time() - start_time) * 1000)
                audit_logger = get_audit_logger()
                audit_logger.log_external_call(
                    audit_log_id=None,
                    service_name='yahoo_finance_search',
                    endpoint_url=url,
                    http_method='GET',
                    request_payload=params,
                    response_payload={'results_count': len(results) if 'results' in dir() else 0},
                    response_status=response_status,
                    execution_time_ms=execution_time_ms,
                    status=status,
                    error_message=error_message,
                )
            except Exception:
                pass  # Don't fail search if logging fails

