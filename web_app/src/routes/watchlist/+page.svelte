<script lang="ts">
  import { onMount } from 'svelte';
  import { Navbar, PriceCard } from '$lib/components';
  import { watchlist, notifications, selectedSymbol } from '$lib/stores/app';
  import { marketApi } from '$lib/api/client';
  import { formatPrice, formatPercent, formatLargeNumber, getPriceColorClass } from '$lib/utils/format';
  import { Plus, Search, Trash2, RefreshCw, X } from 'lucide-svelte';
  import type { Quote, SymbolInfo } from '$lib/api/client';
  import { goto } from '$app/navigation';

  let loading = $state(true);
  let searchQuery = $state('');
  let searchResults = $state<SymbolInfo[]>([]);
  let searching = $state(false);
  let showSearch = $state(false);

  async function fetchQuotes() {
    loading = true;
    const symbols = $watchlist.map(item => item.symbol);

    if (symbols.length === 0) {
      loading = false;
      return;
    }

    const { data, error } = await marketApi.getQuotes(symbols);

    if (error) {
      notifications.add({ type: 'error', message: `Failed to fetch quotes: ${error}` });
    } else if (data) {
      data.forEach((quote: Quote) => {
        watchlist.updateQuote(quote.symbol, quote);
      });
    }

    loading = false;
  }

  async function searchSymbols() {
    if (searchQuery.length < 2) {
      searchResults = [];
      return;
    }

    searching = true;
    const { data, error } = await marketApi.searchSymbols(searchQuery);

    if (!error && data) {
      searchResults = data.filter(s => !$watchlist.find(w => w.symbol === s.symbol));
    }
    searching = false;
  }

  function addToWatchlist(info: SymbolInfo) {
    watchlist.add({ symbol: info.symbol, name: info.name });
    searchResults = searchResults.filter(s => s.symbol !== info.symbol);
    notifications.add({ type: 'success', message: `${info.symbol} added to watchlist` });

    // Fetch quote for new symbol
    marketApi.getQuote(info.symbol).then(({ data }) => {
      if (data) {
        watchlist.updateQuote(info.symbol, data);
      }
    });
  }

  function removeFromWatchlist(symbol: string) {
    watchlist.remove(symbol);
    notifications.add({ type: 'info', message: `${symbol} removed from watchlist` });
  }

  function navigateToChart(symbol: string) {
    selectedSymbol.set(symbol);
    goto('/charts');
  }

  onMount(() => {
    fetchQuotes();
    const interval = setInterval(fetchQuotes, 30000);
    return () => clearInterval(interval);
  });

  let debounceTimer: ReturnType<typeof setTimeout>;
  $effect(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(searchSymbols, 300);
  });
</script>

<div class="flex flex-col h-full">
  <Navbar>
    {#snippet title()}
      <h1 class="text-xl font-semibold text-surface-900 dark:text-white">Watchlist</h1>
    {/snippet}
  </Navbar>

  <div class="flex-1 p-6 overflow-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-surface-900 dark:text-white">Your Watchlist</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400">
          {$watchlist.length} symbols tracked
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <button onclick={fetchQuotes} disabled={loading} class="btn-secondary">
          <RefreshCw class="h-4 w-4 {loading ? 'animate-spin' : ''}" />
        </button>
        <button onclick={() => showSearch = !showSearch} class="btn-primary flex items-center space-x-2">
          <Plus class="h-4 w-4" />
          <span>Add Symbol</span>
        </button>
      </div>
    </div>

    <!-- Search Panel -->
    {#if showSearch}
      <div class="card p-4 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-medium text-surface-900 dark:text-white">Search Symbols</h3>
          <button onclick={() => { showSearch = false; searchQuery = ''; searchResults = []; }} class="p-1 hover:bg-surface-100 dark:hover:bg-surface-700 rounded">
            <X class="h-4 w-4 text-surface-400" />
          </button>
        </div>
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-400" />
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search by symbol or name..."
            class="input pl-10"
          />
        </div>

        {#if searching}
          <div class="mt-4 text-center text-surface-500">Searching...</div>
        {:else if searchResults.length > 0}
          <div class="mt-4 space-y-2 max-h-64 overflow-y-auto">
            {#each searchResults as result}
              <div class="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
                <div>
                  <p class="font-medium text-surface-900 dark:text-white">{result.symbol}</p>
                  <p class="text-sm text-surface-500 dark:text-surface-400">{result.name}</p>
                </div>
                <button
                  onclick={() => addToWatchlist(result)}
                  class="btn-primary py-1.5 px-3 text-sm"
                >
                  <Plus class="h-4 w-4" />
                </button>
              </div>
            {/each}
          </div>
        {:else if searchQuery.length >= 2}
          <div class="mt-4 text-center text-surface-500">No results found</div>
        {/if}
      </div>
    {/if}

    <!-- Watchlist Table -->
    {#if $watchlist.length === 0}
      <div class="card p-12 text-center">
        <Search class="h-16 w-16 mx-auto text-surface-300 dark:text-surface-600 mb-4" />
        <h3 class="text-lg font-medium text-surface-900 dark:text-white mb-2">No symbols in watchlist</h3>
        <p class="text-surface-500 dark:text-surface-400 mb-4">Add symbols to start tracking prices</p>
        <button onclick={() => showSearch = true} class="btn-primary">
          <Plus class="h-4 w-4 mr-2" />
          Add Symbol
        </button>
      </div>
    {:else}
      <div class="card overflow-hidden">
        <table class="w-full">
          <thead class="bg-surface-50 dark:bg-surface-800/50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider">Symbol</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider">Price</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider">Change</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider">Volume</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-200 dark:divide-surface-700">
            {#each $watchlist as item}
              {@const quote = item.quote}
              {@const changePercent = quote?.change_percent ?? 0}
              <tr
                class="hover:bg-surface-50 dark:hover:bg-surface-800/50 cursor-pointer transition-colors"
                onclick={() => navigateToChart(item.symbol)}
              >
                <td class="px-6 py-4">
                  <div>
                    <p class="font-medium text-surface-900 dark:text-white">{item.symbol}</p>
                    {#if item.name}
                      <p class="text-sm text-surface-500 dark:text-surface-400">{item.name}</p>
                    {/if}
                  </div>
                </td>
                <td class="px-6 py-4 text-right">
                  {#if loading && !quote}
                    <div class="h-5 w-20 bg-surface-200 dark:bg-surface-700 rounded animate-pulse ml-auto"></div>
                  {:else if quote}
                    <span class="font-semibold text-surface-900 dark:text-white">{formatPrice(quote.price)}</span>
                  {:else}
                    <span class="text-surface-400">-</span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-right">
                  {#if quote}
                    <span class="{getPriceColorClass(changePercent)} font-medium">
                      {formatPercent(changePercent)}
                    </span>
                  {:else}
                    <span class="text-surface-400">-</span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-right">
                  {#if quote}
                    <span class="text-surface-600 dark:text-surface-300">{formatLargeNumber(quote.volume)}</span>
                  {:else}
                    <span class="text-surface-400">-</span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-right">
                  <button
                    onclick={(e: MouseEvent) => { e.stopPropagation(); removeFromWatchlist(item.symbol); }}
                    class="p-2 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors"
                  >
                    <Trash2 class="h-4 w-4 text-surface-400 hover:text-danger-500" />
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
