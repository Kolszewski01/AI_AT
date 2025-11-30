<script lang="ts">
  import { page } from '$app/stores';
  import {
    LayoutDashboard,
    List,
    BarChart3,
    Zap,
    Bell,
    Settings,
    TrendingUp
  } from 'lucide-svelte';

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Watchlist', href: '/watchlist', icon: List },
    { name: 'Charts', href: '/charts', icon: BarChart3 },
    { name: 'Signals', href: '/signals', icon: Zap },
    { name: 'Alerts', href: '/alerts', icon: Bell },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  function isActive(href: string, pathname: string): boolean {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  }
</script>

<aside class="w-64 bg-white dark:bg-surface-800 border-r border-surface-200 dark:border-surface-700 flex flex-col">
  <!-- Logo -->
  <div class="h-16 flex items-center px-6 border-b border-surface-200 dark:border-surface-700">
    <TrendingUp class="h-8 w-8 text-primary-600" />
    <span class="ml-3 text-xl font-bold text-surface-900 dark:text-white">AI Trading</span>
  </div>

  <!-- Navigation -->
  <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
    {#each navigation as item}
      {@const active = isActive(item.href, $page.url.pathname)}
      <a
        href={item.href}
        class="flex items-center px-3 py-2.5 rounded-lg transition-colors duration-200
          {active
            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
            : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700/50 hover:text-surface-900 dark:hover:text-white'}"
      >
        <svelte:component this={item.icon} class="h-5 w-5 mr-3" />
        <span class="font-medium">{item.name}</span>
      </a>
    {/each}
  </nav>

  <!-- Footer -->
  <div class="p-4 border-t border-surface-200 dark:border-surface-700">
    <div class="text-xs text-surface-500 dark:text-surface-400">
      AI Trading System v0.3.0
    </div>
  </div>
</aside>
