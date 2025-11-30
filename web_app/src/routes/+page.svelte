<script lang="ts">
  import { onMount } from 'svelte';
  import { Navbar, PriceCard, SignalCard, AlertCard } from '$lib/components';
  import { watchlist, signals, alerts, connectionStatus, notifications, selectedSymbol } from '$lib/stores/app';
  import { marketApi, analysisApi, alertsApi, createWebSocket, subscribeToSymbol } from '$lib/api/client';
  import { formatRelativeTime } from '$lib/utils/format';
  import { RefreshCw, TrendingUp, Bell, Zap, ExternalLink } from 'lucide-svelte';
  import type { Quote, Signal } from '$lib/api/client';
  import { goto } from '$app/navigation';

  let loading = $state(true);
  let lastUpdate = $state<Date | null>(null);
  let ws: WebSocket | null = null;

  async function fetchWatchlistQuotes() {
    loading = true;
    const symbols = $watchlist.map(item => item.symbol);

    const { data, error } = await marketApi.getQuotes(symbols);

    if (error) {
      notifications.add({ type: 'error', message: `Failed to fetch quotes: ${error}` });
    } else if (data) {
      data.forEach((quote: Quote) => {
        watchlist.updateQuote(quote.symbol, quote);
      });
      lastUpdate = new Date();
    }

    loading = false;
  }

  async function fetchSignals() {
    const symbolsToFetch = $watchlist.slice(0, 3).map(item => item.symbol);

    const allSignals: Signal[] = [];

    for (const symbol of symbolsToFetch) {
      const { data } = await analysisApi.getSignals(symbol);
      if (data) {
        allSignals.push(...data);
      }
    }

    signals.set(allSignals.slice(0, 5));
  }

  async function fetchAlerts() {
    const { data, error } = await alertsApi.getAll();

    if (!error && data) {
      alerts.set(data);
    }
  }

  function setupWebSocket() {
    connectionStatus.set('connecting');

    ws = createWebSocket((data) => {
      if (data.type === 'quote') {
        watchlist.updateQuote(data.symbol, data.quote);
        lastUpdate = new Date();
      } else if (data.type === 'signal') {
        signals.update(s => [data.signal, ...s].slice(0, 10));
        notifications.add({
          type: data.signal.type === 'BUY' ? 'success' : data.signal.type === 'SELL' ? 'warning' : 'info',
          message: `${data.signal.type} signal for ${data.signal.symbol}`,
        });
      } else if (data.type === 'alert_triggered') {
        alerts.update(data.alert.id, { triggered: true, triggered_at: new Date().toISOString() });
        notifications.add({
          type: 'warning',
          message: `Alert triggered: ${data.alert.symbol} ${data.alert.condition} ${data.alert.target_price}`,
        });
      }
    });

    ws.onopen = () => {
      connectionStatus.set('connected');
      $watchlist.forEach(item => {
        if (ws) subscribeToSymbol(ws, item.symbol);
      });
    };

    ws.onclose = () => {
      connectionStatus.set('disconnected');
    };

    ws.onerror = () => {
      connectionStatus.set('disconnected');
    };
  }

  function handleDeleteAlert(id: string) {
    alertsApi.delete(id).then(({ error }) => {
      if (error) {
        notifications.add({ type: 'error', message: `Failed to delete alert: ${error}` });
      } else {
        alerts.remove(id);
        notifications.add({ type: 'success', message: 'Alert deleted' });
      }
    });
  }

  function navigateToChart(symbol: string) {
    selectedSymbol.set(symbol);
    goto('/charts');
  }

  onMount(() => {
    fetchWatchlistQuotes();
    fetchSignals();
    fetchAlerts();
    setupWebSocket();

    const interval = setInterval(fetchWatchlistQuotes, 30000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  });
</script>

<div class="flex flex-col h-full">
  <Navbar>
    {#snippet title()}
      <h1 class="text-xl font-semibold text-surface-900 dark:text-white">Dashboard</h1>
    {/snippet}
  </Navbar>

  <div class="flex-1 p-6 space-y-6 overflow-auto">
    <!-- Header with refresh -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-surface-900 dark:text-white">Market Overview</h2>
        {#if lastUpdate}
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Last update: {formatRelativeTime(lastUpdate.toISOString())}
          </p>
        {/if}
      </div>
      <button
        onclick={fetchWatchlistQuotes}
        disabled={loading}
        class="btn-secondary flex items-center space-x-2"
      >
        <RefreshCw class="h-4 w-4 {loading ? 'animate-spin' : ''}" />
        <span>Refresh</span>
      </button>
    </div>

    <!-- Watchlist Grid -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-surface-900 dark:text-white flex items-center">
          <TrendingUp class="h-5 w-5 mr-2 text-primary-500" />
          Watchlist
        </h3>
        <a href="/watchlist" class="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center">
          View all <ExternalLink class="h-3 w-3 ml-1" />
        </a>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {#each $watchlist as item}
          <PriceCard
            symbol={item.symbol}
            name={item.name}
            quote={item.quote}
            {loading}
            onclick={() => navigateToChart(item.symbol)}
          />
        {/each}
      </div>
    </section>

    <!-- Signals and Alerts Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Signals -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-surface-900 dark:text-white flex items-center">
            <Zap class="h-5 w-5 mr-2 text-warning-500" />
            Recent Signals
          </h3>
          <a href="/signals" class="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center">
            View all <ExternalLink class="h-3 w-3 ml-1" />
          </a>
        </div>
        {#if $signals.length === 0}
          <div class="card p-8 text-center">
            <Zap class="h-12 w-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
            <p class="text-surface-500 dark:text-surface-400">No signals yet</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each $signals.slice(0, 3) as signal}
              <SignalCard {signal} />
            {/each}
          </div>
        {/if}
      </section>

      <!-- Active Alerts -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-surface-900 dark:text-white flex items-center">
            <Bell class="h-5 w-5 mr-2 text-primary-500" />
            Active Alerts
          </h3>
          <a href="/alerts" class="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center">
            Manage <ExternalLink class="h-3 w-3 ml-1" />
          </a>
        </div>
        {#if $alerts.length === 0}
          <div class="card p-8 text-center">
            <Bell class="h-12 w-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
            <p class="text-surface-500 dark:text-surface-400">No alerts set</p>
            <a href="/alerts" class="btn-primary mt-4 inline-block">Create Alert</a>
          </div>
        {:else}
          <div class="space-y-3">
            {#each $alerts.filter(a => !a.triggered).slice(0, 3) as alert}
              <AlertCard {alert} onDelete={handleDeleteAlert} />
            {/each}
          </div>
        {/if}
      </section>
    </div>
  </div>
</div>
