<script lang="ts">
  import { notifications } from '$lib/stores/app';
  import { fly } from 'svelte/transition';
  import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-svelte';

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    success: 'bg-success-50 dark:bg-success-900/20 border-success-200 dark:border-success-800 text-success-800 dark:text-success-200',
    error: 'bg-danger-50 dark:bg-danger-900/20 border-danger-200 dark:border-danger-800 text-danger-800 dark:text-danger-200',
    warning: 'bg-warning-50 dark:bg-warning-900/20 border-warning-200 dark:border-warning-800 text-warning-800 dark:text-warning-200',
    info: 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800 text-primary-800 dark:text-primary-200',
  };
</script>

<div class="fixed bottom-4 right-4 z-50 space-y-2">
  {#each $notifications as notification (notification.id)}
    <div
      transition:fly={{ x: 100, duration: 300 }}
      class="flex items-center p-4 rounded-lg border shadow-lg {colors[notification.type]}"
    >
      <svelte:component this={icons[notification.type]} class="h-5 w-5 mr-3 flex-shrink-0" />
      <p class="flex-1 text-sm font-medium">{notification.message}</p>
      <button
        onclick={() => notifications.remove(notification.id)}
        class="ml-3 p-1 hover:opacity-70 transition-opacity"
      >
        <X class="h-4 w-4" />
      </button>
    </div>
  {/each}
</div>
