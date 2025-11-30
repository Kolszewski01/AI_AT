<script lang="ts">
  import { formatPrice, formatRelativeTime } from '$lib/utils/format';
  import type { Alert } from '$lib/api/client';
  import { Bell, BellRing, Trash2, ArrowUp, ArrowDown } from 'lucide-svelte';

  interface Props {
    alert: Alert;
    onDelete?: (id: string) => void;
  }

  let { alert, onDelete }: Props = $props();

  const conditionLabel = $derived({
    above: 'Price above',
    below: 'Price below',
    cross_above: 'Crosses above',
    cross_below: 'Crosses below',
  }[alert.condition] || alert.condition);

  const ConditionIcon = $derived(
    alert.condition === 'above' || alert.condition === 'cross_above' ? ArrowUp : ArrowDown
  );
</script>

<div class="card p-4 {alert.triggered ? 'border-warning-500 dark:border-warning-400' : ''}">
  <div class="flex items-start justify-between">
    <div class="flex items-center space-x-3">
      <div class="p-2 rounded-lg {alert.triggered ? 'bg-warning-500/10' : 'bg-primary-500/10'}">
        {#if alert.triggered}
          <BellRing class="h-5 w-5 text-warning-500" />
        {:else}
          <Bell class="h-5 w-5 text-primary-500" />
        {/if}
      </div>
      <div>
        <p class="font-semibold text-surface-900 dark:text-white">{alert.symbol}</p>
        <p class="text-sm text-surface-500 dark:text-surface-400 flex items-center">
          <ConditionIcon class="h-3 w-3 mr-1" />
          {conditionLabel} {formatPrice(alert.target_price)}
        </p>
      </div>
    </div>

    {#if onDelete}
      <button
        onclick={() => onDelete(alert.id)}
        class="p-1.5 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors"
      >
        <Trash2 class="h-4 w-4 text-surface-400 hover:text-danger-500" />
      </button>
    {/if}
  </div>

  {#if alert.current_price}
    <div class="mt-3 text-sm">
      <span class="text-surface-500 dark:text-surface-400">Current: </span>
      <span class="font-medium text-surface-900 dark:text-white">{formatPrice(alert.current_price)}</span>
    </div>
  {/if}

  <div class="mt-3 flex items-center justify-between text-xs text-surface-400">
    <span>Created {formatRelativeTime(alert.created_at)}</span>
    {#if alert.triggered && alert.triggered_at}
      <span class="text-warning-600 dark:text-warning-400">
        Triggered {formatRelativeTime(alert.triggered_at)}
      </span>
    {/if}
  </div>
</div>
