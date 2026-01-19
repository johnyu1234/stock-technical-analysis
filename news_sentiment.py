"""
News and Sentiment Analysis Module
Fetches stock-related news and performs sentiment analysis using VADER.
"""

import yfinance as yf
from datetime import datetime

# Use nltk's VADER for sentiment analysis (no sklearn dependency)
import nltk
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
    from nltk.sentiment.vader import SentimentIntensityAnalyzer


def get_sentiment_analyzer():
    """Get a VADER sentiment analyzer, downloading lexicon if needed."""
    try:
        return SentimentIntensityAnalyzer()
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
        return SentimentIntensityAnalyzer()


def fetch_stock_news(symbol: str, max_news: int = 10) -> list:
    """
    Fetch the latest news for a stock symbol using Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'TSLA', 'AAPL')
        max_news: Maximum number of news articles to fetch
    
    Returns:
        List of news dictionaries with title, publisher, link, and publish time
    """
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            return []
        
        # Limit to max_news items
        news = news[:max_news]
        
        # Process news items - handle both old and new yfinance API formats
        processed_news = []
        for item in news:
            # New format: data is nested in 'content' object
            content = item.get('content', item)
            
            # Get title
            title = content.get('title', '')
            
            # Get publisher - might be in different places
            publisher = content.get('provider', {})
            if isinstance(publisher, dict):
                publisher = publisher.get('displayName', 'Unknown')
            elif not publisher:
                publisher = content.get('publisher', 'Unknown')
            
            # Get link
            link = content.get('clickThroughUrl', {})
            if isinstance(link, dict):
                link = link.get('url', '')
            elif not link:
                link = content.get('link', '')
            
            # Get publish time - try different field names
            pub_time = content.get('pubDate', '')
            if pub_time:
                try:
                    # Parse ISO format date
                    from dateutil import parser
                    dt = parser.parse(pub_time)
                    pub_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pub_time = pub_time[:16] if len(pub_time) > 16 else pub_time
            else:
                # Try old format
                timestamp = item.get('providerPublishTime', 0)
                if timestamp:
                    pub_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                else:
                    pub_time = 'N/A'
            
            processed_news.append({
                'title': title,
                'publisher': publisher,
                'link': link,
                'publish_time': pub_time,
                'type': content.get('contentType', 'news'),
            })
        
        return processed_news
    
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return []


def analyze_sentiment(text: str, analyzer=None) -> dict:
    """
    Perform sentiment analysis using VADER.
    
    Args:
        text: Text to analyze
        analyzer: Optional pre-initialized SentimentIntensityAnalyzer
    
    Returns:
        Dictionary with polarity (-1 to 1), compound score, and sentiment label
    """
    if analyzer is None:
        analyzer = get_sentiment_analyzer()
    
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # Determine sentiment label based on compound score
    if compound >= 0.05:
        label = 'POSITIVE'
    elif compound <= -0.05:
        label = 'NEGATIVE'
    else:
        label = 'NEUTRAL'
    
    return {
        'polarity': compound,
        'positive': scores['pos'],
        'negative': scores['neg'],
        'neutral': scores['neu'],
        'label': label
    }


def analyze_news_sentiment(news_list: list) -> dict:
    """
    Analyze sentiment for a list of news articles.
    
    Args:
        news_list: List of news dictionaries with 'title' key
    
    Returns:
        Dictionary with individual sentiments and overall analysis
    """
    if not news_list:
        return {
            'articles': [],
            'overall': {'label': 'N/A', 'average_polarity': 0, 'summary': 'No news available'}
        }
    
    analyzer = get_sentiment_analyzer()
    analyzed_articles = []
    total_polarity = 0
    
    for article in news_list:
        title = article.get('title', '')
        sentiment = analyze_sentiment(title, analyzer)
        
        analyzed_articles.append({
            'title': title,
            'publisher': article.get('publisher', ''),
            'publish_time': article.get('publish_time', ''),
            'link': article.get('link', ''),
            'sentiment': sentiment
        })
        
        total_polarity += sentiment['polarity']
    
    # Calculate overall sentiment
    avg_polarity = total_polarity / len(news_list)
    
    if avg_polarity >= 0.05:
        overall_label = 'BULLISH'
        summary = 'News sentiment is predominantly positive'
    elif avg_polarity <= -0.05:
        overall_label = 'BEARISH'
        summary = 'News sentiment is predominantly negative'
    else:
        overall_label = 'NEUTRAL'
        summary = 'News sentiment is mixed or neutral'
    
    # Count sentiment distribution
    positive_count = sum(1 for a in analyzed_articles if a['sentiment']['label'] == 'POSITIVE')
    negative_count = sum(1 for a in analyzed_articles if a['sentiment']['label'] == 'NEGATIVE')
    neutral_count = sum(1 for a in analyzed_articles if a['sentiment']['label'] == 'NEUTRAL')
    
    return {
        'articles': analyzed_articles,
        'overall': {
            'label': overall_label,
            'average_polarity': avg_polarity,
            'summary': summary,
            'distribution': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            }
        }
    }


def print_news_analysis(symbol: str, sentiment_results: dict):
    """
    Print formatted news sentiment analysis.
    """
    print("\n" + "=" * 60)
    print(f"  NEWS SENTIMENT ANALYSIS: {symbol}")
    print("=" * 60)
    
    overall = sentiment_results.get('overall', {})
    dist = overall.get('distribution', {})
    
    # Overall sentiment
    emoji = "🟢" if overall.get('label') == 'BULLISH' else "🔴" if overall.get('label') == 'BEARISH' else "⚪"
    print(f"\n  {emoji} Overall Sentiment: {overall.get('label', 'N/A')}")
    print(f"     Average Polarity: {overall.get('average_polarity', 0):.3f}")
    print(f"     {overall.get('summary', '')}")
    print(f"\n     📊 Distribution: {dist.get('positive', 0)} Positive | {dist.get('neutral', 0)} Neutral | {dist.get('negative', 0)} Negative")
    
    print("\n" + "-" * 60)
    print("  TOP NEWS HEADLINES")
    print("-" * 60)
    
    articles = sentiment_results.get('articles', [])
    for i, article in enumerate(articles, 1):
        sentiment = article.get('sentiment', {})
        polarity = sentiment.get('polarity', 0)
        label = sentiment.get('label', 'NEUTRAL')
        
        # Emoji based on sentiment
        if label == 'POSITIVE':
            emoji = "🟢"
        elif label == 'NEGATIVE':
            emoji = "🔴"
        else:
            emoji = "⚪"
        
        print(f"\n  {i}. {emoji} [{label}] (polarity: {polarity:.2f})")
        print(f"     📰 {article.get('title', 'N/A')}")
        print(f"     📡 {article.get('publisher', 'N/A')} | {article.get('publish_time', 'N/A')}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Test the module
    symbol = "TSLA"
    print(f"\nFetching news for {symbol}...")
    
    news = fetch_stock_news(symbol, max_news=10)
    print(f"Found {len(news)} news articles")
    
    sentiment_results = analyze_news_sentiment(news)
    print_news_analysis(symbol, sentiment_results)
