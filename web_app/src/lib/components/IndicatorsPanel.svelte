<script lang="ts">
  import type { TechnicalIndicators } from '$lib/api/client';
  import { formatPrice } from '$lib/utils/format';

  interface Props {
    indicators: TechnicalIndicators | null;
    loading?: boolean;
  }

  let { indicators, loading = false }: Props = $props();

  function getRsiColor(rsi: number | null): string {
    if (rsi === null) return 'text-surface-500';
    if (rsi >= 70) return 'text-danger-500';
    if (rsi <= 30) return 'text-success-500';
    return 'text-surface-700 dark:text-surface-300';
  }

  function getRsiLabel(rsi: number | null): string {
    if (rsi === null) return '-';
    if (rsi >= 70) return 'Overbought';
    if (rsi <= 30) return 'Oversold';
    return 'Neutral';
  }

  function getMacdSignal(macd: { macd: number; signal: number; histogram: number } | null): string {
    if (!macd) return '-';
    if (macd.histogram > 0) return 'Bullish';
    if (macd.histogram < 0) return 'Bearish';
    return 'Neutral';
  }
</script>

<div class="card p-4">
  <h3 class="font-semibold text-surface-900 dark:text-white mb-4">Technical Indicators</h3>

  {#if loading}
    <div class="space-y-3">
      {#each Array(6) as _}
        <div class="h-12 bg-surface-100 dark:bg-surface-700 rounded animate-pulse"></div>
      {/each}
    </div>
  {:else if indicators}
    <div class="space-y-4">
      <!-- RSI -->
      <div class="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
        <div>
          <p class="text-sm text-surface-500 dark:text-surface-400">RSI (14)</p>
          <p class="text-lg font-semibold {getRsiColor(indicators.rsi)}">
            {indicators.rsi?.toFixed(2) ?? '-'}
          </p>
        </div>
        <span class="text-xs px-2 py-1 rounded {getRsiColor(indicators.rsi)} bg-current/10">
          {getRsiLabel(indicators.rsi)}
        </span>
      </div>

      <!-- MACD -->
      <div class="p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm text-surface-500 dark:text-surface-400">MACD</p>
          <span class="text-xs px-2 py-1 rounded {indicators.macd?.histogram && indicators.macd.histogram > 0 ? 'text-success-500 bg-success-500/10' : 'text-danger-500 bg-danger-500/10'}">
            {getMacdSignal(indicators.macd)}
          </span>
        </div>
        {#if indicators.macd}
          <div class="grid grid-cols-3 gap-2 text-sm">
            <div>
              <p class="text-xs text-surface-400">MACD</p>
              <p class="font-medium text-surface-700 dark:text-surface-300">{indicators.macd.macd.toFixed(4)}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Signal</p>
              <p class="font-medium text-surface-700 dark:text-surface-300">{indicators.macd.signal.toFixed(4)}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Histogram</p>
              <p class="font-medium {indicators.macd.histogram > 0 ? 'text-success-500' : 'text-danger-500'}">{indicators.macd.histogram.toFixed(4)}</p>
            </div>
          </div>
        {:else}
          <p class="text-surface-400">-</p>
        {/if}
      </div>

      <!-- Moving Averages -->
      <div class="p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
        <p class="text-sm text-surface-500 dark:text-surface-400 mb-2">Moving Averages</p>
        <div class="grid grid-cols-3 gap-2 text-sm">
          <div>
            <p class="text-xs text-surface-400">SMA 20</p>
            <p class="font-medium text-surface-700 dark:text-surface-300">{formatPrice(indicators.sma_20 ?? 0)}</p>
          </div>
          <div>
            <p class="text-xs text-surface-400">SMA 50</p>
            <p class="font-medium text-surface-700 dark:text-surface-300">{formatPrice(indicators.sma_50 ?? 0)}</p>
          </div>
          <div>
            <p class="text-xs text-surface-400">SMA 200</p>
            <p class="font-medium text-surface-700 dark:text-surface-300">{formatPrice(indicators.sma_200 ?? 0)}</p>
          </div>
        </div>
      </div>

      <!-- Bollinger Bands -->
      {#if indicators.bollinger}
        <div class="p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
          <p class="text-sm text-surface-500 dark:text-surface-400 mb-2">Bollinger Bands</p>
          <div class="grid grid-cols-3 gap-2 text-sm">
            <div>
              <p class="text-xs text-surface-400">Upper</p>
              <p class="font-medium text-danger-500">{formatPrice(indicators.bollinger.upper)}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Middle</p>
              <p class="font-medium text-surface-700 dark:text-surface-300">{formatPrice(indicators.bollinger.middle)}</p>
            </div>
            <div>
              <p class="text-xs text-surface-400">Lower</p>
              <p class="font-medium text-success-500">{formatPrice(indicators.bollinger.lower)}</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- ATR & ADX -->
      <div class="grid grid-cols-2 gap-3">
        <div class="p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
          <p class="text-xs text-surface-400">ATR</p>
          <p class="text-lg font-semibold text-surface-700 dark:text-surface-300">
            {indicators.atr?.toFixed(4) ?? '-'}
          </p>
        </div>
        <div class="p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
          <p class="text-xs text-surface-400">ADX</p>
          <p class="text-lg font-semibold text-surface-700 dark:text-surface-300">
            {indicators.adx?.toFixed(2) ?? '-'}
          </p>
        </div>
      </div>
    </div>
  {:else}
    <p class="text-surface-500 dark:text-surface-400 text-center py-8">No data available</p>
  {/if}
</div>
