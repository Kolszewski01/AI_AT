import { writable, derived } from 'svelte/store';
import type { Quote, Alert, Signal } from '$lib/api/client';

// Theme store
export const theme = writable<'light' | 'dark'>('dark');

// Initialize theme from localStorage
if (typeof window !== 'undefined') {
  const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
  if (savedTheme) {
    theme.set(savedTheme);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme.set('dark');
  }
}

theme.subscribe((value) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('theme', value);
    if (value === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
});

// Watchlist store
export interface WatchlistItem {
  symbol: string;
  name?: string;
  quote?: Quote;
}

const defaultWatchlist: WatchlistItem[] = [
  { symbol: '^GDAXI', name: 'DAX' },
  { symbol: '^GSPC', name: 'S&P 500' },
  { symbol: 'BTC-USD', name: 'Bitcoin' },
  { symbol: 'ETH-USD', name: 'Ethereum' },
  { symbol: 'EURUSD=X', name: 'EUR/USD' },
];

function createWatchlistStore() {
  const stored = typeof window !== 'undefined'
    ? localStorage.getItem('watchlist')
    : null;

  const initial = stored ? JSON.parse(stored) : defaultWatchlist;
  const { subscribe, set, update } = writable<WatchlistItem[]>(initial);

  return {
    subscribe,
    add: (item: WatchlistItem) => update(items => {
      if (items.find(i => i.symbol === item.symbol)) return items;
      const newItems = [...items, item];
      if (typeof window !== 'undefined') {
        localStorage.setItem('watchlist', JSON.stringify(newItems));
      }
      return newItems;
    }),
    remove: (symbol: string) => update(items => {
      const newItems = items.filter(i => i.symbol !== symbol);
      if (typeof window !== 'undefined') {
        localStorage.setItem('watchlist', JSON.stringify(newItems));
      }
      return newItems;
    }),
    updateQuote: (symbol: string, quote: Quote) => update(items =>
      items.map(item => item.symbol === symbol ? { ...item, quote } : item)
    ),
    reset: () => {
      set(defaultWatchlist);
      if (typeof window !== 'undefined') {
        localStorage.setItem('watchlist', JSON.stringify(defaultWatchlist));
      }
    }
  };
}

export const watchlist = createWatchlistStore();

// Alerts store
function createAlertsStore() {
  const { subscribe, set, update } = writable<Alert[]>([]);

  return {
    subscribe,
    set,
    add: (alert: Alert) => update(alerts => [...alerts, alert]),
    remove: (id: string) => update(alerts => alerts.filter(a => a.id !== id)),
    update: (id: string, data: Partial<Alert>) => update(alerts =>
      alerts.map(a => a.id === id ? { ...a, ...data } : a)
    ),
  };
}

export const alerts = createAlertsStore();

// Signals store
export const signals = writable<Signal[]>([]);

// Selected symbol for charts
export const selectedSymbol = writable<string>('^GDAXI');

// Connection status
export const connectionStatus = writable<'connected' | 'disconnected' | 'connecting'>('disconnected');

// Notifications
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timeout?: number;
}

function createNotificationStore() {
  const { subscribe, update } = writable<Notification[]>([]);

  return {
    subscribe,
    add: (notification: Omit<Notification, 'id'>) => {
      const id = crypto.randomUUID();
      update(n => [...n, { ...notification, id }]);

      if (notification.timeout !== 0) {
        setTimeout(() => {
          update(n => n.filter(item => item.id !== id));
        }, notification.timeout || 5000);
      }

      return id;
    },
    remove: (id: string) => update(n => n.filter(item => item.id !== id)),
    clear: () => update(() => []),
  };
}

export const notifications = createNotificationStore();

// Derived stores
export const activeAlerts = derived(alerts, $alerts =>
  $alerts.filter(a => !a.triggered)
);

export const triggeredAlerts = derived(alerts, $alerts =>
  $alerts.filter(a => a.triggered)
);
