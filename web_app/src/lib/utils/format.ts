import { format, formatDistanceToNow, parseISO } from 'date-fns';

// Format price with appropriate decimal places
export function formatPrice(price: number, decimals: number = 2): string {
  if (price === null || price === undefined || isNaN(price)) return '-';

  // Crypto usually has more decimals
  if (price < 1) {
    return price.toFixed(6);
  } else if (price < 10) {
    return price.toFixed(4);
  } else if (price < 1000) {
    return price.toFixed(decimals);
  } else {
    return price.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }
}

// Format percentage change
export function formatPercent(value: number, includeSign: boolean = true): string {
  if (value === null || value === undefined || isNaN(value)) return '-';

  const sign = includeSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

// Format large numbers (volume, market cap, etc.)
export function formatLargeNumber(value: number): string {
  if (value === null || value === undefined || isNaN(value)) return '-';

  if (value >= 1e12) {
    return `${(value / 1e12).toFixed(2)}T`;
  } else if (value >= 1e9) {
    return `${(value / 1e9).toFixed(2)}B`;
  } else if (value >= 1e6) {
    return `${(value / 1e6).toFixed(2)}M`;
  } else if (value >= 1e3) {
    return `${(value / 1e3).toFixed(2)}K`;
  }
  return value.toLocaleString();
}

// Format date/time
export function formatDateTime(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy HH:mm');
  } catch {
    return dateString;
  }
}

export function formatDate(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy');
  } catch {
    return dateString;
  }
}

export function formatTime(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return format(date, 'HH:mm:ss');
  } catch {
    return dateString;
  }
}

export function formatRelativeTime(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return dateString;
  }
}

// Get color class based on value (positive/negative)
export function getPriceColorClass(value: number): string {
  if (value > 0) return 'text-bullish';
  if (value < 0) return 'text-bearish';
  return 'text-surface-500';
}

export function getPriceBgClass(value: number): string {
  if (value > 0) return 'bg-bullish';
  if (value < 0) return 'bg-bearish';
  return 'bg-surface-100 dark:bg-surface-800';
}

// Signal type to badge class
export function getSignalBadgeClass(type: string): string {
  switch (type.toUpperCase()) {
    case 'BUY':
      return 'badge-success';
    case 'SELL':
      return 'badge-danger';
    case 'HOLD':
      return 'badge-warning';
    default:
      return 'badge-primary';
  }
}

// Truncate text
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}
