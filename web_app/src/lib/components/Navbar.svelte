<script lang="ts">
  import { theme, connectionStatus, notifications } from '$lib/stores/app';
  import { Sun, Moon, Wifi, WifiOff, Bell, X } from 'lucide-svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    title?: Snippet;
    children?: Snippet;
  }

  let { title, children }: Props = $props();

  function toggleTheme() {
    theme.update(t => t === 'dark' ? 'light' : 'dark');
  }

  let showNotifications = $state(false);

  function dismissNotification(id: string) {
    notifications.remove(id);
  }
</script>

<header class="h-16 bg-white dark:bg-surface-800 border-b border-surface-200 dark:border-surface-700 flex items-center justify-between px-6">
  <!-- Page title slot -->
  <div class="flex items-center">
    {#if title}
      {@render title()}
    {:else if children}
      {@render children()}
    {:else}
      <h1 class="text-xl font-semibold text-surface-900 dark:text-white">Dashboard</h1>
    {/if}
  </div>

  <!-- Right side actions -->
  <div class="flex items-center space-x-4">
    <!-- Connection status -->
    <div class="flex items-center space-x-2">
      {#if $connectionStatus === 'connected'}
        <Wifi class="h-5 w-5 text-success-500" />
        <span class="text-sm text-success-600 dark:text-success-400">Connected</span>
      {:else if $connectionStatus === 'connecting'}
        <Wifi class="h-5 w-5 text-warning-500 animate-pulse" />
        <span class="text-sm text-warning-600 dark:text-warning-400">Connecting...</span>
      {:else}
        <WifiOff class="h-5 w-5 text-danger-500" />
        <span class="text-sm text-danger-600 dark:text-danger-400">Disconnected</span>
      {/if}
    </div>

    <!-- Notifications -->
    <div class="relative">
      <button
        onclick={() => showNotifications = !showNotifications}
        class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors relative"
      >
        <Bell class="h-5 w-5 text-surface-600 dark:text-surface-400" />
        {#if $notifications.length > 0}
          <span class="absolute top-1 right-1 h-2 w-2 bg-danger-500 rounded-full"></span>
        {/if}
      </button>

      {#if showNotifications && $notifications.length > 0}
        <div class="absolute right-0 mt-2 w-80 bg-white dark:bg-surface-800 rounded-xl shadow-lg border border-surface-200 dark:border-surface-700 z-50">
          <div class="p-3 border-b border-surface-200 dark:border-surface-700">
            <h3 class="font-medium text-surface-900 dark:text-white">Notifications</h3>
          </div>
          <div class="max-h-64 overflow-y-auto">
            {#each $notifications as notification}
              <div class="p-3 border-b border-surface-100 dark:border-surface-700 last:border-0 flex items-start justify-between">
                <div class="flex-1">
                  <p class="text-sm text-surface-700 dark:text-surface-300">{notification.message}</p>
                </div>
                <button
                  onclick={() => dismissNotification(notification.id)}
                  class="ml-2 p-1 hover:bg-surface-100 dark:hover:bg-surface-700 rounded"
                >
                  <X class="h-4 w-4 text-surface-400" />
                </button>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>

    <!-- Theme toggle -->
    <button
      onclick={toggleTheme}
      class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
      aria-label="Toggle theme"
    >
      {#if $theme === 'dark'}
        <Sun class="h-5 w-5 text-surface-400" />
      {:else}
        <Moon class="h-5 w-5 text-surface-600" />
      {/if}
    </button>
  </div>
</header>
