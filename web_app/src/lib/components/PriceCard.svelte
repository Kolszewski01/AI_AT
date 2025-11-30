<script lang="ts">
  import { formatPrice, formatPercent, getPriceColorClass } from '$lib/utils/format';
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';
  import type { Quote } from '$lib/api/client';

  interface Props {
    symbol: string;
    name?: string;
    quote?: Quote;
    loading?: boolean;
    onclick?: () => void;
  }

  let { symbol, name, quote, loading = false, onclick }: Props = $props();

  const changePercent = $derived(quote?.change_percent ?? 0);
  const TrendIcon = $derived(changePercent > 0 ? TrendingUp : changePercent < 0 ? TrendingDown : Minus);
</script>

<button
  type="button"
  class="card p-4 w-full text-left hover:shadow-md transition-shadow cursor-pointer"
  onclick={onclick}
>
  <div class="flex items-start justify-between">
    <div>
      <p class="text-sm font-medium text-surface-500 dark:text-surface-400">{symbol}</p>
      {#if name}
        <p class="text-xs text-surface-400 dark:text-surface-500 truncate">{name}</p>
      {/if}
    </div>
    {#if quote}
      <div class="flex items-center {getPriceColorClass(changePercent)}">
        <TrendIcon class="h-4 w-4" />
      </div>
    {/if}
  </div>

  {#if loading}
    <div class="mt-3 space-y-2">
      <div class="h-6 bg-surface-200 dark:bg-surface-700 rounded animate-pulse"></div>
      <div class="h-4 w-20 bg-surface-200 dark:bg-surface-700 rounded animate-pulse"></div>
    </div>
  {:else if quote}
    <div class="mt-3">
      <p class="text-2xl font-bold text-surface-900 dark:text-white">
        {formatPrice(quote.price)}
      </p>
      <p class="text-sm {getPriceColorClass(changePercent)}">
        {formatPercent(changePercent)}
      </p>
    </div>
  {:else}
    <div class="mt-3">
      <p class="text-sm text-surface-400">No data</p>
    </div>
  {/if}
</button>
