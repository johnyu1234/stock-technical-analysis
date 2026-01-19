/**
 * Stock Technical Analysis Dashboard
 * Interactive JavaScript frontend with Chart.js
 */

// Chart instances
let priceChart = null;
let volumeChart = null;
let macdChart = null;
let rsiChart = null;

// Current data
let currentData = null;
let currentSymbol = 'TSLA';
let chartType = 'line'; // 'line' or 'candlestick'

// Chart.js default configuration
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#1e293b';
Chart.defaults.font.family = "'Inter', sans-serif";

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadStockData('TSLA', '6mo');
});

function setupEventListeners() {
    document.getElementById('analyzeBtn').addEventListener('click', () => {
        const symbol = document.getElementById('symbolInput').value.trim().toUpperCase();
        const period = document.getElementById('periodSelect').value;
        if (symbol) {
            loadStockData(symbol, period);
        }
    });

    document.getElementById('symbolInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('analyzeBtn').click();
        }
    });

    // Chart type toggle buttons
    document.getElementById('chartTypeToggle').addEventListener('click', () => {
        setChartType('line');
    });

    document.getElementById('candlestickToggle').addEventListener('click', () => {
        setChartType('candlestick');
    });

    // Autocomplete functionality
    const symbolInput = document.getElementById('symbolInput');
    const dropdown = document.getElementById('autocompleteDropdown');
    let searchTimeout;
    let selectedIndex = -1;

    symbolInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        clearTimeout(searchTimeout);

        if (query.length < 1) {
            dropdown.innerHTML = '';
            dropdown.classList.remove('visible');
            return;
        }

        // Debounce search
        searchTimeout = setTimeout(() => {
            searchStocks(query);
        }, 300);
    });

    symbolInput.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.autocomplete-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection(items);
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            items[selectedIndex].click();
        } else if (e.key === 'Escape') {
            dropdown.classList.remove('visible');
            selectedIndex = -1;
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!symbolInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('visible');
            selectedIndex = -1;
        }
    });
}

function setChartType(type) {
    if (chartType === type) return;

    chartType = type;

    // Update button states
    document.getElementById('chartTypeToggle').classList.toggle('active', type === 'line');
    document.getElementById('candlestickToggle').classList.toggle('active', type === 'candlestick');

    // Recreate price chart with new type
    if (currentData) {
        const chartData = currentData.data;
        const labels = chartData.map(d => d.Date);
        createPriceChart(labels, chartData);
    }
}

async function loadStockData(symbol, period) {
    showLoading(true);
    currentSymbol = symbol;

    try {
        // Fetch stock data
        const stockResponse = await fetch(`/api/stock/${symbol}?period=${period}`);
        const stockData = await stockResponse.json();

        if (!stockData.success) {
            throw new Error(stockData.error || 'Failed to fetch stock data');
        }

        currentData = stockData;

        // Update UI
        updateStockInfo(stockData);
        updateCharts(stockData);
        updateSignals(stockData.signals);
        updateRecommendations(stockData.recommendations);

        // Fetch news separately
        loadNewsData(symbol);

    } catch (error) {
        console.error('Error loading stock data:', error);
        alert('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function loadNewsData(symbol) {
    try {
        const newsResponse = await fetch(`/api/news/${symbol}`);
        const newsData = await newsResponse.json();

        if (newsData.success) {
            updateNewsSentiment(newsData.sentiment);
        }
    } catch (error) {
        console.error('Error loading news:', error);
    }
}

function updateStockInfo(data) {
    const info = data.info;
    const latestData = data.data[data.data.length - 1];
    const previousData = data.data[data.data.length - 2];

    document.getElementById('stockName').textContent = info.name || data.symbol;
    document.getElementById('stockSymbol').textContent = data.symbol;
    document.getElementById('stockSector').textContent = `📁 ${info.sector || 'N/A'}`;
    document.getElementById('stockIndustry').textContent = `🏭 ${info.industry || 'N/A'}`;

    const currentPrice = latestData.Close;
    const previousPrice = previousData ? previousData.Close : currentPrice;
    const change = currentPrice - previousPrice;
    const changePercent = ((change / previousPrice) * 100).toFixed(2);

    document.getElementById('currentPrice').textContent = `$${currentPrice.toFixed(2)}`;

    const priceChangeEl = document.getElementById('priceChange');
    priceChangeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent}%)`;
    priceChangeEl.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
}

function updateCharts(data) {
    const chartData = data.data;
    const labels = chartData.map(d => d.Date);

    createPriceChart(labels, chartData);
    createVolumeChart(labels, chartData);
    createMACDChart(labels, chartData);
    createRSIChart(labels, chartData);
}

function createPriceChart(labels, data) {
    const ctx = document.getElementById('priceChart').getContext('2d');

    if (priceChart) priceChart.destroy();

    if (chartType === 'candlestick') {
        createCandlestickChart(ctx, labels, data);
    } else {
        createLineChart(ctx, labels, data);
    }
}

function createCandlestickChart(ctx, labels, data) {
    // Prepare candlestick data
    const candlestickData = data.map((d, i) => ({
        x: new Date(d.Date).getTime(),
        o: d.Open,
        h: d.High,
        l: d.Low,
        c: d.Close
    }));

    priceChart = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [
                {
                    label: 'OHLC',
                    data: candlestickData,
                    color: {
                        up: '#10b981',
                        down: '#ef4444',
                        unchanged: '#94a3b8'
                    },
                    borderColor: {
                        up: '#10b981',
                        down: '#ef4444',
                        unchanged: '#94a3b8'
                    }
                },
                {
                    type: 'line',
                    label: 'SMA 20',
                    data: data.map(d => ({ x: new Date(d.Date).getTime(), y: d.SMA_20 })),
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0,
                },
                {
                    type: 'line',
                    label: 'SMA 50',
                    data: data.map(d => ({ x: new Date(d.Date).getTime(), y: d.SMA_50 })),
                    borderColor: '#ef4444',
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0,
                },
                {
                    type: 'line',
                    label: 'BB Upper',
                    data: data.map(d => ({ x: new Date(d.Date).getTime(), y: d.BB_Upper })),
                    borderColor: 'rgba(168, 85, 247, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                },
                {
                    type: 'line',
                    label: 'BB Lower',
                    data: data.map(d => ({ x: new Date(d.Date).getTime(), y: d.BB_Lower })),
                    borderColor: 'rgba(168, 85, 247, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(26, 31, 46, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#1e293b',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        title: (items) => {
                            if (!items.length) return '';
                            const date = new Date(items[0].parsed.x);
                            return `📅 ${date.toISOString().split('T')[0]}`;
                        },
                        label: (context) => {
                            if (context.dataset.type === 'candlestick' || context.datasetIndex === 0) {
                                const d = context.raw;
                                return [
                                    `  Open: $${d.o?.toFixed(2)}`,
                                    `  High: $${d.h?.toFixed(2)}`,
                                    `  Low: $${d.l?.toFixed(2)}`,
                                    `  Close: $${d.c?.toFixed(2)}`
                                ];
                            }
                            const value = context.parsed.y;
                            if (value === null || value === undefined) return null;
                            return `  ${context.dataset.label}: $${value.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'yyyy-MM-dd'
                        }
                    },
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 10,
                        font: { size: 10 }
                    }
                },
                y: {
                    position: 'right',
                    grid: { color: 'rgba(30, 41, 59, 0.5)' },
                    ticks: {
                        callback: (value) => '$' + value.toFixed(0),
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}

function createLineChart(ctx, labels, data) {
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Close',
                    data: data.map(d => d.Close),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#3b82f6',
                },
                {
                    label: 'SMA 20',
                    data: data.map(d => d.SMA_20),
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                },
                {
                    label: 'SMA 50',
                    data: data.map(d => d.SMA_50),
                    borderColor: '#ef4444',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                },
                {
                    label: 'BB Upper',
                    data: data.map(d => d.BB_Upper),
                    borderColor: 'rgba(168, 85, 247, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                },
                {
                    label: 'BB Lower',
                    data: data.map(d => d.BB_Lower),
                    borderColor: 'rgba(168, 85, 247, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: '-1',
                    backgroundColor: 'rgba(168, 85, 247, 0.05)',
                    pointRadius: 0,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(26, 31, 46, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#1e293b',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: (items) => {
                            const idx = items[0].dataIndex;
                            const d = data[idx];
                            return `📅 ${d.Date}`;
                        },
                        afterTitle: (items) => {
                            const idx = items[0].dataIndex;
                            const d = data[idx];
                            return `\n📊 OHLC: O:$${d.Open?.toFixed(2)} H:$${d.High?.toFixed(2)} L:$${d.Low?.toFixed(2)} C:$${d.Close?.toFixed(2)}`;
                        },
                        label: (context) => {
                            const value = context.parsed.y;
                            if (value === null || value === undefined) return null;
                            return `  ${context.dataset.label}: $${value.toFixed(2)}`;
                        },
                        afterBody: (items) => {
                            const idx = items[0].dataIndex;
                            const d = data[idx];
                            const vol = d.Volume ? (d.Volume / 1e6).toFixed(2) : 'N/A';
                            return `\n📈 Volume: ${vol}M`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 10,
                        font: { size: 10 }
                    }
                },
                y: {
                    position: 'right',
                    grid: { color: 'rgba(30, 41, 59, 0.5)' },
                    ticks: {
                        callback: (value) => '$' + value.toFixed(0),
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}

function createVolumeChart(labels, data) {
    const ctx = document.getElementById('volumeChart').getContext('2d');

    if (volumeChart) volumeChart.destroy();

    const colors = data.map((d, i) => {
        if (i === 0) return '#3b82f6';
        return d.Close >= data[i - 1].Close ? '#10b981' : '#ef4444';
    });

    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volume',
                data: data.map(d => d.Volume),
                backgroundColor: colors.map(c => c + '80'),
                borderColor: colors,
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(26, 31, 46, 0.95)',
                    callbacks: {
                        title: (items) => `📅 ${data[items[0].dataIndex].Date}`,
                        label: (context) => {
                            const vol = context.parsed.y;
                            return `📊 Volume: ${(vol / 1e6).toFixed(2)}M`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { display: false }
                },
                y: {
                    position: 'right',
                    grid: { color: 'rgba(30, 41, 59, 0.5)' },
                    ticks: {
                        callback: (value) => (value / 1e6).toFixed(0) + 'M',
                        font: { size: 10 },
                        maxTicksLimit: 3
                    }
                }
            }
        }
    });
}

function createMACDChart(labels, data) {
    const ctx = document.getElementById('macdChart').getContext('2d');

    if (macdChart) macdChart.destroy();

    const histColors = data.map(d => d.MACD_Histogram >= 0 ? '#10b981' : '#ef4444');

    macdChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    type: 'line',
                    label: 'MACD',
                    data: data.map(d => d.MACD),
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    order: 1
                },
                {
                    type: 'line',
                    label: 'Signal',
                    data: data.map(d => d.MACD_Signal),
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    order: 2
                },
                {
                    type: 'bar',
                    label: 'Histogram',
                    data: data.map(d => d.MACD_Histogram),
                    backgroundColor: histColors.map(c => c + '80'),
                    borderColor: histColors,
                    borderWidth: 1,
                    order: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 10,
                        font: { size: 10 }
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(26, 31, 46, 0.95)',
                    callbacks: {
                        title: (items) => `📅 ${data[items[0].dataIndex].Date}`,
                        label: (context) => {
                            const value = context.parsed.y;
                            if (value === null) return null;
                            return `  ${context.dataset.label}: ${value.toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { display: false }
                },
                y: {
                    position: 'right',
                    grid: { color: 'rgba(30, 41, 59, 0.5)' },
                    ticks: { font: { size: 10 }, maxTicksLimit: 4 }
                }
            }
        }
    });
}

function createRSIChart(labels, data) {
    const ctx = document.getElementById('rsiChart').getContext('2d');

    if (rsiChart) rsiChart.destroy();

    rsiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'RSI',
                data: data.map(d => d.RSI),
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 5,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(26, 31, 46, 0.95)',
                    callbacks: {
                        title: (items) => `📅 ${data[items[0].dataIndex].Date}`,
                        label: (context) => {
                            const rsi = context.parsed.y;
                            let status = 'Neutral';
                            if (rsi > 70) status = '⚠️ Overbought';
                            else if (rsi < 30) status = '⚠️ Oversold';
                            return [`  RSI: ${rsi.toFixed(2)}`, `  ${status}`];
                        }
                    }
                },
                annotation: {
                    annotations: {
                        overbought: {
                            type: 'line',
                            yMin: 70,
                            yMax: 70,
                            borderColor: 'rgba(239, 68, 68, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        oversold: {
                            type: 'line',
                            yMin: 30,
                            yMax: 30,
                            borderColor: 'rgba(16, 185, 129, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { display: false }
                },
                y: {
                    position: 'right',
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(30, 41, 59, 0.5)' },
                    ticks: {
                        font: { size: 10 },
                        stepSize: 20,
                        callback: (value) => {
                            if (value === 70) return '70 ↑';
                            if (value === 30) return '30 ↓';
                            return value;
                        }
                    }
                }
            }
        }
    });

    // Draw threshold lines manually
    const yScale = rsiChart.scales.y;
    const ctx2 = rsiChart.ctx;

    // After chart is drawn, add threshold lines
    rsiChart.options.animation = {
        onComplete: () => {
            const y70 = yScale.getPixelForValue(70);
            const y30 = yScale.getPixelForValue(30);

            ctx2.save();
            ctx2.setLineDash([5, 5]);
            ctx2.strokeStyle = 'rgba(239, 68, 68, 0.5)';
            ctx2.beginPath();
            ctx2.moveTo(rsiChart.chartArea.left, y70);
            ctx2.lineTo(rsiChart.chartArea.right, y70);
            ctx2.stroke();

            ctx2.strokeStyle = 'rgba(16, 185, 129, 0.5)';
            ctx2.beginPath();
            ctx2.moveTo(rsiChart.chartArea.left, y30);
            ctx2.lineTo(rsiChart.chartArea.right, y30);
            ctx2.stroke();
            ctx2.restore();
        }
    };
}

function updateSignals(signals) {
    const grid = document.getElementById('signalsGrid');

    if (!signals) {
        grid.innerHTML = '<div class="signal-card">No signals available</div>';
        return;
    }

    const signalCards = [];

    // Trend Signal
    if (signals.trend) {
        const trend = signals.trend;
        const signalClass = trend.signal.includes('UP') ? 'signal-bullish' :
            trend.signal.includes('DOWN') ? 'signal-bearish' : 'signal-neutral';
        signalCards.push(`
            <div class="signal-card ${signalClass}">
                <div class="signal-label">📈 Trend</div>
                <div class="signal-value">${trend.signal}</div>
                <div class="signal-description">${trend.description}</div>
            </div>
        `);
    }

    // RSI Signal
    if (signals.rsi) {
        const rsi = signals.rsi;
        const signalClass = rsi.signal === 'OVERSOLD' ? 'signal-bullish' :
            rsi.signal === 'OVERBOUGHT' ? 'signal-bearish' : 'signal-neutral';
        signalCards.push(`
            <div class="signal-card ${signalClass}">
                <div class="signal-label">📊 RSI (${rsi.value?.toFixed(1) || 'N/A'})</div>
                <div class="signal-value">${rsi.signal}</div>
                <div class="signal-description">${rsi.description}</div>
            </div>
        `);
    }

    // MACD Signal
    if (signals.macd) {
        const macd = signals.macd;
        const signalClass = macd.signal.includes('BULLISH') ? 'signal-bullish' :
            macd.signal.includes('BEARISH') ? 'signal-bearish' : 'signal-neutral';
        signalCards.push(`
            <div class="signal-card ${signalClass}">
                <div class="signal-label">📉 MACD</div>
                <div class="signal-value">${macd.signal}</div>
                <div class="signal-description">${macd.description}</div>
            </div>
        `);
    }

    // Bollinger Signal
    if (signals.bollinger) {
        const bb = signals.bollinger;
        const signalClass = bb.signal.includes('UPPER') ? 'signal-bearish' :
            bb.signal.includes('LOWER') ? 'signal-bullish' : 'signal-neutral';
        signalCards.push(`
            <div class="signal-card ${signalClass}">
                <div class="signal-label">📐 Bollinger Bands</div>
                <div class="signal-value">${bb.signal}</div>
                <div class="signal-description">${bb.description}</div>
            </div>
        `);
    }

    grid.innerHTML = signalCards.join('');
}

function updateNewsSentiment(sentiment) {
    const summaryEl = document.getElementById('sentimentSummary');
    const listEl = document.getElementById('newsList');

    const overall = sentiment.overall;
    const dist = overall.distribution || {};

    const sentimentClass = overall.label === 'BULLISH' ? 'sentiment-bullish' :
        overall.label === 'BEARISH' ? 'sentiment-bearish' : 'sentiment-neutral';

    summaryEl.innerHTML = `
        <div>
            <span class="sentiment-label ${sentimentClass}">
                ${overall.label === 'BULLISH' ? '🟢' : overall.label === 'BEARISH' ? '🔴' : '⚪'} 
                ${overall.label}
            </span>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">
                ${overall.summary}
            </div>
        </div>
        <div class="sentiment-stats">
            <span style="color: var(--success);">✓ ${dist.positive || 0}</span>
            <span style="color: var(--warning);">○ ${dist.neutral || 0}</span>
            <span style="color: var(--danger);">✗ ${dist.negative || 0}</span>
        </div>
    `;

    // News articles
    const articles = sentiment.articles || [];
    if (articles.length === 0) {
        listEl.innerHTML = '<div class="loading">No news articles found</div>';
        return;
    }

    listEl.innerHTML = articles.map(article => {
        const sent = article.sentiment;
        const itemClass = sent.label === 'POSITIVE' ? 'positive' :
            sent.label === 'NEGATIVE' ? 'negative' : 'neutral';
        const badgeClass = sent.label === 'POSITIVE' ? 'badge-positive' :
            sent.label === 'NEGATIVE' ? 'badge-negative' : 'badge-neutral';

        const linkUrl = article.link || '#';
        const hasLink = article.link && article.link.length > 0;

        return `
            <a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="news-item-link ${hasLink ? '' : 'no-link'}">
                <div class="news-item ${itemClass}">
                    <div class="news-title">
                        ${article.title}
                        <span class="news-sentiment-badge ${badgeClass}">${sent.label}</span>
                        ${hasLink ? '<span class="link-icon">🔗</span>' : ''}
                    </div>
                    <div class="news-meta">
                        ${article.publisher} • ${article.publish_time}
                        • Polarity: ${sent.polarity?.toFixed(2) || 'N/A'}
                    </div>
                </div>
            </a>
        `;
    }).join('');
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('visible');
    } else {
        overlay.classList.remove('visible');
    }
}

async function searchStocks(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.success && data.results.length > 0) {
            displayAutocomplete(data.results);
        } else {
            const dropdown = document.getElementById('autocompleteDropdown');
            dropdown.innerHTML = '<div class="autocomplete-empty">No results found</div>';
            dropdown.classList.add('visible');
        }
    } catch (error) {
        console.error('Search error:', error);
    }
}

function displayAutocomplete(results) {
    const dropdown = document.getElementById('autocompleteDropdown');

    dropdown.innerHTML = results.map(stock => `
        <div class="autocomplete-item" data-symbol="${stock.symbol}">
            <div class="autocomplete-symbol">${stock.symbol}</div>
            <div class="autocomplete-name">${stock.name}</div>
            ${stock.exchange ? `<div class="autocomplete-exchange">${stock.exchange}</div>` : ''}
        </div>
    `).join('');

    dropdown.classList.add('visible');

    // Add click handlers
    dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
            const symbol = item.dataset.symbol;
            document.getElementById('symbolInput').value = symbol;
            dropdown.classList.remove('visible');
            // Optionally trigger analysis
            // document.getElementById('analyzeBtn').click();
        });
    });
}


function updateSelection(items) {
    items.forEach((item, index) => {
        if (index === selectedIndex) {
            item.classList.add('selected');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('selected');
        }
    });
}

function updateRecommendations(recommendations) {
    console.log('updateRecommendations called with:', recommendations);

    if (!recommendations || Object.keys(recommendations).length === 0) {
        console.log('No recommendations data');
        return;
    }

    const grid = document.getElementById('signalsGrid');
    console.log('Signals grid element:', grid);

    // Determine overall verdict (use 'today' as primary recommendation)
    const primaryRec = recommendations.today || {};
    console.log('Primary recommendation:', primaryRec);

    const colorClass = primaryRec.color === 'success' ? 'signal-bullish' :
        primaryRec.color === 'danger' ? 'signal-bearish' : 'signal-neutral';

    const actionEmoji = primaryRec.action?.includes('BUY') ? '🟢' :
        primaryRec.action?.includes('SELL') ? '🔴' : '⚪';

    // Create timeframe breakdown for tooltip
    const timeframes = [
        { key: 'today', label: 'Today', icon: '📅' },
        { key: 'week', label: 'This Week', icon: '📆' },
        { key: 'month', label: 'This Month', icon: '📋' },
        { key: 'year', label: 'This Year', icon: '🗓️' }
    ];

    const timeframeDetailsHTML = timeframes.map(tf => {
        const rec = recommendations[tf.key];
        if (!rec) return '';

        const emoji = rec.action.includes('BUY') ? '🟢' :
            rec.action.includes('SELL') ? '🔴' : '⚪';

        return `<div class="tooltip-row">${tf.icon} ${tf.label}: ${emoji} ${rec.action} (${rec.confidence.toFixed(0)}%)</div>`;
    }).join('');

    const verdictCard = `
        <div class="signal-card ${colorClass} verdict-card">
            <div class="signal-label">🎯 Verdict</div>
            <div class="signal-value">${actionEmoji} ${primaryRec.action || 'N/A'}</div>
            <div class="signal-description">${primaryRec.confidence?.toFixed(0) || 0}%</div>
            <div class="verdict-tooltip">
                <div class="tooltip-title">Timeframe Analysis</div>
                ${timeframeDetailsHTML}
            </div>
        </div>
    `;

    console.log('Verdict card HTML:', verdictCard);
    console.log('Grid innerHTML before:', grid.innerHTML.substring(0, 100));

    // Prepend verdict to the signals grid
    grid.innerHTML = verdictCard + grid.innerHTML;

    console.log('Grid innerHTML after:', grid.innerHTML.substring(0, 200));
}
