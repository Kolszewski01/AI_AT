<script lang="ts">
  import '../app.css';
  import { Sidebar, NotificationToast } from '$lib/components';
  import { onMount } from 'svelte';
  import { theme } from '$lib/stores/app';

  let { children } = $props();

  onMount(() => {
    // Apply initial theme
    const currentTheme = $theme;
    if (currentTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  });
</script>

<svelte:head>
  <title>AI Trading System</title>
  <meta name="description" content="AI-powered trading analysis and signals" />
</svelte:head>

<div class="flex h-screen overflow-hidden bg-surface-50 dark:bg-surface-900">
  <Sidebar />

  <main class="flex-1 overflow-auto">
    {@render children()}
  </main>
</div>

<NotificationToast />
