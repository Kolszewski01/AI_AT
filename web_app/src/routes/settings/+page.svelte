<script lang="ts">
  import { Navbar } from '$lib/components';
  import { theme, watchlist, notifications } from '$lib/stores/app';
  import { marketApi } from '$lib/api/client';
  import { Sun, Moon, Monitor, RotateCcw, Server, Wifi } from 'lucide-svelte';

  let backendStatus = $state<'checking' | 'connected' | 'disconnected'>('checking');
  let rateLimit = $state<{ remaining: number; limit: number } | null>(null);

  async function checkBackendStatus() {
    backendStatus = 'checking';

    const { data, error } = await marketApi.getStatus();

    if (error) {
      backendStatus = 'disconnected';
    } else if (data) {
      backendStatus = 'connected';
      if (data.rate_limit) {
        rateLimit = data.rate_limit as { remaining: number; limit: number };
      }
    }
  }

  function resetWatchlist() {
    watchlist.reset();
    notifications.add({ type: 'success', message: 'Watchlist reset to defaults' });
  }

  function clearLocalStorage() {
    if (typeof window !== 'undefined') {
      localStorage.clear();
      notifications.add({ type: 'info', message: 'Local storage cleared. Refreshing...' });
      setTimeout(() => window.location.reload(), 1000);
    }
  }

  // Check backend status on mount
  $effect(() => {
    checkBackendStatus();
  });
</script>

<div class="flex flex-col h-full">
  <Navbar>
    {#snippet title()}
      <h1 class="text-xl font-semibold text-surface-900 dark:text-white">Settings</h1>
    {/snippet}
  </Navbar>

  <div class="flex-1 p-6 overflow-auto">
    <div class="max-w-2xl mx-auto space-y-6">
      <!-- Appearance -->
      <section class="card p-6">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Appearance</h2>

        <div class="space-y-4">
          <div>
            <span class="label">Theme</span>
            <div class="grid grid-cols-3 gap-3 mt-2" role="radiogroup" aria-label="Theme selection">
              <button
                onclick={() => theme.set('light')}
                class="flex flex-col items-center p-4 rounded-lg border-2 transition-colors
                  {$theme === 'light'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-surface-200 dark:border-surface-700 hover:border-surface-300 dark:hover:border-surface-600'}"
              >
                <Sun class="h-6 w-6 mb-2 {$theme === 'light' ? 'text-primary-500' : 'text-surface-400'}" />
                <span class="text-sm font-medium {$theme === 'light' ? 'text-primary-700 dark:text-primary-300' : 'text-surface-600 dark:text-surface-400'}">
                  Light
                </span>
              </button>

              <button
                onclick={() => theme.set('dark')}
                class="flex flex-col items-center p-4 rounded-lg border-2 transition-colors
                  {$theme === 'dark'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-surface-200 dark:border-surface-700 hover:border-surface-300 dark:hover:border-surface-600'}"
              >
                <Moon class="h-6 w-6 mb-2 {$theme === 'dark' ? 'text-primary-500' : 'text-surface-400'}" />
                <span class="text-sm font-medium {$theme === 'dark' ? 'text-primary-700 dark:text-primary-300' : 'text-surface-600 dark:text-surface-400'}">
                  Dark
                </span>
              </button>

              <button
                disabled
                class="flex flex-col items-center p-4 rounded-lg border-2 border-surface-200 dark:border-surface-700 opacity-50 cursor-not-allowed"
              >
                <Monitor class="h-6 w-6 mb-2 text-surface-400" />
                <span class="text-sm font-medium text-surface-400">System</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Backend Status -->
      <section class="card p-6">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Backend Connection</h2>

        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
            <div class="flex items-center space-x-3">
              <Server class="h-5 w-5 text-surface-500" />
              <div>
                <p class="font-medium text-surface-900 dark:text-white">API Server</p>
                <p class="text-sm text-surface-500">http://localhost:8000</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              {#if backendStatus === 'checking'}
                <div class="h-3 w-3 rounded-full bg-surface-400 animate-pulse"></div>
                <span class="text-sm text-surface-500">Checking...</span>
              {:else if backendStatus === 'connected'}
                <div class="h-3 w-3 rounded-full bg-success-500"></div>
                <span class="text-sm text-success-600 dark:text-success-400">Connected</span>
              {:else}
                <div class="h-3 w-3 rounded-full bg-danger-500"></div>
                <span class="text-sm text-danger-600 dark:text-danger-400">Disconnected</span>
              {/if}
            </div>
          </div>

          {#if rateLimit}
            <div class="flex items-center justify-between p-4 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
              <div class="flex items-center space-x-3">
                <Wifi class="h-5 w-5 text-surface-500" />
                <div>
                  <p class="font-medium text-surface-900 dark:text-white">Rate Limit</p>
                  <p class="text-sm text-surface-500">Yahoo Finance API</p>
                </div>
              </div>
              <span class="text-sm text-surface-600 dark:text-surface-400">
                {rateLimit.remaining} / {rateLimit.limit}
              </span>
            </div>
          {/if}

          <button onclick={checkBackendStatus} class="btn-secondary w-full">
            Check Connection
          </button>
        </div>
      </section>

      <!-- Data Management -->
      <section class="card p-6">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">Data Management</h2>

        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">Watchlist</p>
              <p class="text-sm text-surface-500">{$watchlist.length} symbols tracked</p>
            </div>
            <button onclick={resetWatchlist} class="btn-secondary flex items-center space-x-2">
              <RotateCcw class="h-4 w-4" />
              <span>Reset</span>
            </button>
          </div>

          <div class="flex items-center justify-between p-4 bg-surface-50 dark:bg-surface-700/50 rounded-lg">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">Local Storage</p>
              <p class="text-sm text-surface-500">Theme, watchlist, preferences</p>
            </div>
            <button onclick={clearLocalStorage} class="btn-danger flex items-center space-x-2">
              <RotateCcw class="h-4 w-4" />
              <span>Clear All</span>
            </button>
          </div>
        </div>
      </section>

      <!-- About -->
      <section class="card p-6">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-white mb-4">About</h2>

        <div class="space-y-2 text-sm text-surface-600 dark:text-surface-400">
          <p><strong>AI Trading System</strong> - Web Application</p>
          <p>Version: 0.3.0</p>
          <p>Built with SvelteKit, Tailwind CSS, and Lightweight Charts</p>
        </div>
      </section>
    </div>
  </div>
</div>
