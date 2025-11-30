<script lang="ts">
  import { onMount } from 'svelte';
  import { Navbar } from '$lib/components';
  import TradingChart from '$lib/components/TradingChart.svelte';
  import IndicatorsPanel from '$lib/components/IndicatorsPanel.svelte';
  import { selectedSymbol, watchlist, notifications } from '$lib/stores/app';
  import { marketApi, analysisApi } from '$lib/api/client';
  import { formatPrice, formatPercent, getPriceColorClass } from '$lib/utils/format';
  import type { OHLCV, Quote, TechnicalIndicators } from '$lib/api/client';
  import { ChevronDown, RefreshCw } from 'lucide-svelte';

  let ohlcvData = $state<OHLCV[]>([]);
  let quote = $state<Quote | null>(null);
  let indicators = $state<TechnicalIndicators | null>(null);
  let loading = $state(true);
  let indicatorsLoading = $state(true);

  let interval = $state('1d');
  let period = $state('3mo');

  const intervals = [
    { value: '1m', label: '1 Min' },
    { value: '5m', label: '5 Min' },
    { value: '15m', label: '15 Min' },
    { value: '1h', label: '1 Hour' },
    { value: '1d', label: '1 Day' },
    { value: '1wk', label: '1 Week' },
  ];

  const periods = [
    { value: '1d', label: '1 Day' },
    { value: '5d', label: '5 Days' },
    { value: '1mo', label: '1 Month' },
    { value: '3mo', label: '3 Months' },
    { value: '6mo', label: '6 Months' },
    { value: '1y', label: '1 Year' },
    { value: '2y', label: '2 Years' },
  ];

  async function fetchChartData() {
    loading = true;

    const { data, error } = await marketApi.getOHLCV($selectedSymbol, interval, period);

    if (error) {
      notifications.add({ type: 'error', message: `Failed to fetch chart data: ${error}` });
      ohlcvData = [];
    } else if (data) {
      ohlcvData = data;
    }

    loading = false;
  }

  async function fetchQuote() {
    const { data } = await marketApi.getQuote($selectedSymbol);
    if (data) {
      quote = data;
    }
  }

  async function fetchIndicators() {
    indicatorsLoading = true;

    const { data, error } = await analysisApi.getIndicators($selectedSymbol);

    if (!error && data) {
      indicators = data;
    }

    indicatorsLoading = false;
  }

  function changeSymbol(symbol: string) {
    selectedSymbol.set(symbol);
  }

  $effect(() => {
    $selectedSymbol;
    fetchChartData();
    fetchQuote();
    fetchIndicators();
  });

  $effect(() => {
    interval;
    period;
    fetchChartData();
  });

  onMount(() => {
    const quoteInterval = setInterval(fetchQuote, 10000);
    return () => clearInterval(quoteInterval);
  });
</script>

<div class="flex flex-col h-full">
  <Navbar>
    {#snippet title()}
      <h1 class="text-xl font-semibold text-surface-900 dark:text-white">Charts</h1>
    {/snippet}
  </Navbar>

  <div class="flex-1 p-6 overflow-auto">
    <!-- Header -->
    <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div class="flex items-center space-x-4">
        <!-- Symbol selector -->
        <div class="relative">
          <select
            bind:value={$selectedSymbol}
            class="input pr-10 appearance-none min-w-[200px]"
          >
            {#each $watchlist as item}
              <option value={item.symbol}>{item.symbol} - {item.name || ''}</option>
            {/each}
          </select>
          <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-400 pointer-events-none" />
        </div>

        <!-- Quote info -->
        {#if quote}
          <div class="flex items-baseline space-x-3">
            <span class="text-3xl font-bold text-surface-900 dark:text-white">
              {formatPrice(quote.price)}
            </span>
            <span class="{getPriceColorClass(quote.change_percent)} text-lg font-medium">
              {formatPercent(quote.change_percent)}
            </span>
          </div>
        {/if}
      </div>

      <div class="flex items-center space-x-3">
        <!-- Interval selector -->
        <div class="flex bg-surface-100 dark:bg-surface-800 rounded-lg p-1">
          {#each intervals as int}
            <button
              onclick={() => interval = int.value}
              class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors
                {interval === int.value
                  ? 'bg-white dark:bg-surface-700 text-surface-900 dark:text-white shadow-sm'
                  : 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white'}"
            >
              {int.label}
            </button>
          {/each}
        </div>

        <!-- Period selector -->
        <div class="relative">
          <select bind:value={period} class="input pr-10 appearance-none">
            {#each periods as p}
              <option value={p.value}>{p.label}</option>
            {/each}
          </select>
          <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-400 pointer-events-none" />
        </div>

        <button onclick={fetchChartData} disabled={loading} class="btn-secondary">
          <RefreshCw class="h-4 w-4 {loading ? 'animate-spin' : ''}" />
        </button>
      </div>
    </div>

    <!-- Chart and Indicators -->
    <div class="grid grid-cols-1 xl:grid-cols-4 gap-6">
      <!-- Chart -->
      <div class="xl:col-span-3 card p-4">
        {#if loading && ohlcvData.length === 0}
          <div class="h-[500px] flex items-center justify-center">
            <RefreshCw class="h-8 w-8 text-surface-400 animate-spin" />
          </div>
        {:else if ohlcvData.length === 0}
          <div class="h-[500px] flex items-center justify-center">
            <p class="text-surface-500 dark:text-surface-400">No data available</p>
          </div>
        {:else}
          <div class="h-[500px]">
            <TradingChart data={ohlcvData} symbol={$selectedSymbol} />
          </div>
        {/if}
      </div>

      <!-- Indicators Panel -->
      <div class="xl:col-span-1">
        <IndicatorsPanel {indicators} loading={indicatorsLoading} />
      </div>
    </div>
  </div>
</div>
