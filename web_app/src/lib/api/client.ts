// API Client for AI Trading System Backend
// Connects to FastAPI backend at localhost:8000

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = response.ok ? await response.json() : null;
    const error = !response.ok ? `HTTP ${response.status}: ${response.statusText}` : null;

    return { data, error, status: response.status };
  } catch (err) {
    return {
      data: null,
      error: err instanceof Error ? err.message : 'Unknown error',
      status: 0,
    };
  }
}

// ============ Market Data API ============

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

export interface OHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SymbolInfo {
  symbol: string;
  name: string;
  type: string;
  exchange: string;
}

export const marketApi = {
  getQuote: (symbol: string) =>
    fetchApi<Quote>(`/market/quote/${symbol}`),

  getQuotes: (symbols: string[]) =>
    fetchApi<Quote[]>(`/market/quotes?symbols=${symbols.join(',')}`),

  getOHLCV: (symbol: string, interval: string = '1d', period: string = '1mo') =>
    fetchApi<OHLCV[]>(`/market/ohlcv/${symbol}?interval=${interval}&period=${period}`),

  searchSymbols: (query: string) =>
    fetchApi<SymbolInfo[]>(`/market/search?q=${query}`),

  getStatus: () =>
    fetchApi<{ status: string; rate_limit: object }>('/market/status'),
};

// ============ Analysis API ============

export interface TechnicalIndicators {
  symbol: string;
  rsi: number | null;
  macd: { macd: number; signal: number; histogram: number } | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  ema_12: number | null;
  ema_26: number | null;
  bollinger: { upper: number; middle: number; lower: number } | null;
  atr: number | null;
  adx: number | null;
}

export interface Signal {
  symbol: string;
  type: 'BUY' | 'SELL' | 'HOLD';
  strength: number;
  reason: string;
  timestamp: string;
  indicators: string[];
}

export interface SupportResistance {
  support_levels: number[];
  resistance_levels: number[];
}

export const analysisApi = {
  getIndicators: (symbol: string) =>
    fetchApi<TechnicalIndicators>(`/analysis/indicators/${symbol}`),

  getSignals: (symbol: string) =>
    fetchApi<Signal[]>(`/analysis/signals/${symbol}`),

  getSupportResistance: (symbol: string) =>
    fetchApi<SupportResistance>(`/analysis/support-resistance/${symbol}`),

  getPatterns: (symbol: string) =>
    fetchApi<{ patterns: string[] }>(`/analysis/patterns/${symbol}`),
};

// ============ Alerts API ============

export interface Alert {
  id: string;
  symbol: string;
  condition: 'above' | 'below' | 'cross_above' | 'cross_below';
  target_price: number;
  current_price?: number;
  triggered: boolean;
  triggered_at?: string;
  created_at: string;
  notification_type: 'push' | 'email' | 'both';
  message?: string;
}

export interface CreateAlertRequest {
  symbol: string;
  condition: string;
  target_price: number;
  notification_type?: string;
  message?: string;
}

export const alertsApi = {
  getAll: () =>
    fetchApi<Alert[]>('/alerts'),

  create: (alert: CreateAlertRequest) =>
    fetchApi<Alert>('/alerts', {
      method: 'POST',
      body: JSON.stringify(alert),
    }),

  delete: (id: string) =>
    fetchApi<void>(`/alerts/${id}`, { method: 'DELETE' }),

  update: (id: string, alert: Partial<CreateAlertRequest>) =>
    fetchApi<Alert>(`/alerts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(alert),
    }),
};

// ============ News API ============

export interface NewsItem {
  title: string;
  summary: string;
  url: string;
  source: string;
  published_at: string;
  sentiment?: number;
  symbols?: string[];
}

export const newsApi = {
  getLatest: (symbol?: string) =>
    fetchApi<NewsItem[]>(symbol ? `/news?symbol=${symbol}` : '/news'),

  getSentiment: (symbol: string) =>
    fetchApi<{ symbol: string; sentiment: number; articles_analyzed: number }>(
      `/news/sentiment/${symbol}`
    ),
};

// ============ Risk API ============

export interface PositionSize {
  position_size: number;
  risk_amount: number;
  stop_loss_pips: number;
  take_profit_pips: number;
  risk_reward_ratio: number;
}

export const riskApi = {
  calculatePositionSize: (params: {
    account_size: number;
    risk_percent: number;
    entry_price: number;
    stop_loss: number;
    take_profit?: number;
  }) =>
    fetchApi<PositionSize>('/risk/position-size', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
};

// ============ WebSocket ============

export function createWebSocket(onMessage: (data: any) => void): WebSocket {
  const ws = new WebSocket('ws://localhost:8000/ws');

  ws.onopen = () => {
    console.log('[WS] Connected to backend');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('[WS] Failed to parse message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('[WS] Error:', error);
  };

  ws.onclose = () => {
    console.log('[WS] Disconnected');
  };

  return ws;
}

export function subscribeToSymbol(ws: WebSocket, symbol: string) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'subscribe', symbol }));
  }
}

export function unsubscribeFromSymbol(ws: WebSocket, symbol: string) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'unsubscribe', symbol }));
  }
}
