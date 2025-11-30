<script lang="ts">
  import { onMount } from 'svelte';
  import { Navbar, AlertCard } from '$lib/components';
  import { alerts, watchlist, notifications } from '$lib/stores/app';
  import { alertsApi, marketApi } from '$lib/api/client';
  import { formatPrice } from '$lib/utils/format';
  import type { Alert, CreateAlertRequest, Quote } from '$lib/api/client';
  import { Plus, Bell, BellRing, X } from 'lucide-svelte';

  let loading = $state(true);
  let showCreateModal = $state(false);
  let creating = $state(false);

  // Form state
  let newAlert = $state<CreateAlertRequest>({
    symbol: '',
    condition: 'above',
    target_price: 0,
    notification_type: 'push',
    message: '',
  });

  let currentPrice = $state<number | null>(null);

  const activeAlerts = $derived($alerts.filter(a => !a.triggered));
  const triggeredAlerts = $derived($alerts.filter(a => a.triggered));

  async function fetchAlerts() {
    loading = true;
    const { data, error } = await alertsApi.getAll();

    if (error) {
      notifications.add({ type: 'error', message: `Failed to fetch alerts: ${error}` });
    } else if (data) {
      alerts.set(data);
    }

    loading = false;
  }

  async function fetchCurrentPrice() {
    if (!newAlert.symbol) {
      currentPrice = null;
      return;
    }

    const { data } = await marketApi.getQuote(newAlert.symbol);
    if (data) {
      currentPrice = data.price;
      if (newAlert.target_price === 0) {
        newAlert.target_price = data.price;
      }
    }
  }

  async function createAlert() {
    if (!newAlert.symbol || newAlert.target_price <= 0) {
      notifications.add({ type: 'error', message: 'Please fill in all required fields' });
      return;
    }

    creating = true;

    const { data, error } = await alertsApi.create(newAlert);

    if (error) {
      notifications.add({ type: 'error', message: `Failed to create alert: ${error}` });
    } else if (data) {
      alerts.add(data);
      notifications.add({ type: 'success', message: 'Alert created successfully' });
      showCreateModal = false;
      resetForm();
    }

    creating = false;
  }

  async function deleteAlert(id: string) {
    const { error } = await alertsApi.delete(id);

    if (error) {
      notifications.add({ type: 'error', message: `Failed to delete alert: ${error}` });
    } else {
      alerts.remove(id);
      notifications.add({ type: 'success', message: 'Alert deleted' });
    }
  }

  function resetForm() {
    newAlert = {
      symbol: '',
      condition: 'above',
      target_price: 0,
      notification_type: 'push',
      message: '',
    };
    currentPrice = null;
  }

  $effect(() => {
    newAlert.symbol;
    fetchCurrentPrice();
  });

  onMount(() => {
    fetchAlerts();
  });
</script>

<div class="flex flex-col h-full">
  <Navbar>
    {#snippet title()}
      <h1 class="text-xl font-semibold text-surface-900 dark:text-white">Alerts</h1>
    {/snippet}
  </Navbar>

  <div class="flex-1 p-6 overflow-auto">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-2xl font-bold text-surface-900 dark:text-white">Price Alerts</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400">
          {activeAlerts.length} active, {triggeredAlerts.length} triggered
        </p>
      </div>
      <button onclick={() => showCreateModal = true} class="btn-primary flex items-center space-x-2">
        <Plus class="h-4 w-4" />
        <span>Create Alert</span>
      </button>
    </div>

    <!-- Active Alerts -->
    <section class="mb-8">
      <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center">
        <Bell class="h-5 w-5 mr-2 text-primary-500" />
        Active Alerts
      </h3>

      {#if loading}
        <div class="space-y-4">
          {#each Array(3) as _}
            <div class="card p-4 animate-pulse">
              <div class="h-16 bg-surface-200 dark:bg-surface-700 rounded"></div>
            </div>
          {/each}
        </div>
      {:else if activeAlerts.length === 0}
        <div class="card p-8 text-center">
          <Bell class="h-12 w-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
          <p class="text-surface-500 dark:text-surface-400">No active alerts</p>
          <button onclick={() => showCreateModal = true} class="btn-primary mt-4">
            Create your first alert
          </button>
        </div>
      {:else}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {#each activeAlerts as alert}
            <AlertCard {alert} onDelete={deleteAlert} />
          {/each}
        </div>
      {/if}
    </section>

    <!-- Triggered Alerts -->
    {#if triggeredAlerts.length > 0}
      <section>
        <h3 class="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center">
          <BellRing class="h-5 w-5 mr-2 text-warning-500" />
          Triggered Alerts
        </h3>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {#each triggeredAlerts as alert}
            <AlertCard {alert} onDelete={deleteAlert} />
          {/each}
        </div>
      </section>
    {/if}
  </div>
</div>

<!-- Create Alert Modal -->
{#if showCreateModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <button
      type="button"
      class="absolute inset-0 bg-black/50 cursor-default"
      onclick={() => showCreateModal = false}
      aria-label="Close modal"
    ></button>
    <div class="relative bg-white dark:bg-surface-800 rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-surface-900 dark:text-white">Create Alert</h2>
        <button onclick={() => { showCreateModal = false; resetForm(); }} class="p-2 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg">
          <X class="h-5 w-5 text-surface-400" />
        </button>
      </div>

      <form onsubmit={(e: SubmitEvent) => { e.preventDefault(); createAlert(); }} class="space-y-4">
        <!-- Symbol -->
        <div>
          <label for="symbol" class="label">Symbol</label>
          <select id="symbol" bind:value={newAlert.symbol} class="input" required>
            <option value="">Select a symbol</option>
            {#each $watchlist as item}
              <option value={item.symbol}>{item.symbol} - {item.name || ''}</option>
            {/each}
          </select>
          {#if currentPrice}
            <p class="text-sm text-surface-500 mt-1">Current price: {formatPrice(currentPrice)}</p>
          {/if}
        </div>

        <!-- Condition -->
        <div>
          <label for="condition" class="label">Condition</label>
          <select id="condition" bind:value={newAlert.condition} class="input">
            <option value="above">Price goes above</option>
            <option value="below">Price goes below</option>
            <option value="cross_above">Price crosses above</option>
            <option value="cross_below">Price crosses below</option>
          </select>
        </div>

        <!-- Target Price -->
        <div>
          <label for="target_price" class="label">Target Price</label>
          <input
            type="number"
            id="target_price"
            bind:value={newAlert.target_price}
            step="0.01"
            min="0"
            class="input"
            required
          />
        </div>

        <!-- Notification Type -->
        <div>
          <label for="notification_type" class="label">Notification</label>
          <select id="notification_type" bind:value={newAlert.notification_type} class="input">
            <option value="push">Push notification</option>
            <option value="email">Email</option>
            <option value="both">Both</option>
          </select>
        </div>

        <!-- Message -->
        <div>
          <label for="message" class="label">Message (optional)</label>
          <input
            type="text"
            id="message"
            bind:value={newAlert.message}
            placeholder="Custom alert message"
            class="input"
          />
        </div>

        <div class="flex justify-end space-x-3 pt-4">
          <button type="button" onclick={() => { showCreateModal = false; resetForm(); }} class="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={creating} class="btn-primary">
            {creating ? 'Creating...' : 'Create Alert'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
