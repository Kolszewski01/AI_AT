<script lang="ts">
  import { formatRelativeTime, getSignalBadgeClass } from '$lib/utils/format';
  import type { Signal } from '$lib/api/client';
  import { TrendingUp, TrendingDown, Pause } from 'lucide-svelte';

  interface Props {
    signal: Signal;
  }

  let { signal }: Props = $props();

  const SignalIcon = $derived(
    signal.type === 'BUY' ? TrendingUp :
    signal.type === 'SELL' ? TrendingDown : Pause
  );
</script>

<div class="card p-4">
  <div class="flex items-start justify-between">
    <div class="flex items-center space-x-3">
      <div class="p-2 rounded-lg {signal.type === 'BUY' ? 'bg-success-500/10' : signal.type === 'SELL' ? 'bg-danger-500/10' : 'bg-warning-500/10'}">
        <SignalIcon class="h-5 w-5 {signal.type === 'BUY' ? 'text-success-500' : signal.type === 'SELL' ? 'text-danger-500' : 'text-warning-500'}" />
      </div>
      <div>
        <p class="font-semibold text-surface-900 dark:text-white">{signal.symbol}</p>
        <p class="text-sm text-surface-500 dark:text-surface-400">
          {formatRelativeTime(signal.timestamp)}
        </p>
      </div>
    </div>
    <span class="{getSignalBadgeClass(signal.type)}">{signal.type}</span>
  </div>

  <div class="mt-3">
    <p class="text-sm text-surface-600 dark:text-surface-300">{signal.reason}</p>
  </div>

  {#if signal.indicators && signal.indicators.length > 0}
    <div class="mt-3 flex flex-wrap gap-1">
      {#each signal.indicators as indicator}
        <span class="px-2 py-0.5 text-xs bg-surface-100 dark:bg-surface-700 rounded text-surface-600 dark:text-surface-400">
          {indicator}
        </span>
      {/each}
    </div>
  {/if}

  <div class="mt-3 flex items-center justify-between">
    <span class="text-xs text-surface-400">Strength</span>
    <div class="flex-1 mx-3 h-1.5 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full {signal.type === 'BUY' ? 'bg-success-500' : signal.type === 'SELL' ? 'bg-danger-500' : 'bg-warning-500'}"
        style="width: {signal.strength * 100}%"
      ></div>
    </div>
    <span class="text-xs font-medium text-surface-600 dark:text-surface-300">
      {(signal.strength * 100).toFixed(0)}%
    </span>
  </div>
</div>
