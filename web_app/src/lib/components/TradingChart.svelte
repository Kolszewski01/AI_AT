<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
  import type { IChartApi, ISeriesApi, CandlestickData, HistogramData, Time } from 'lightweight-charts';
  import { theme } from '$lib/stores/app';
  import type { OHLCV } from '$lib/api/client';

  interface Props {
    data: OHLCV[];
    symbol: string;
  }

  let { data, symbol }: Props = $props();

  let chartContainer: HTMLDivElement;
  let chart: IChartApi | null = null;
  let candlestickSeries: ISeriesApi<'Candlestick'> | null = null;
  let volumeSeries: ISeriesApi<'Histogram'> | null = null;

  function getChartColors(isDark: boolean) {
    return {
      background: isDark ? '#1e293b' : '#ffffff',
      text: isDark ? '#94a3b8' : '#64748b',
      grid: isDark ? '#334155' : '#e2e8f0',
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    };
  }

  function formatChartData(ohlcvData: OHLCV[]): CandlestickData<Time>[] {
    return ohlcvData.map(d => ({
      time: d.timestamp.split('T')[0] as Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    })).sort((a, b) => (a.time as string).localeCompare(b.time as string));
  }

  function formatVolumeData(ohlcvData: OHLCV[]): HistogramData<Time>[] {
    return ohlcvData.map(d => ({
      time: d.timestamp.split('T')[0] as Time,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    })).sort((a, b) => (a.time as string).localeCompare(b.time as string));
  }

  function initChart() {
    if (!chartContainer) return;

    const isDark = $theme === 'dark';
    const colors = getChartColors(isDark);

    chart = createChart(chartContainer, {
      layout: {
        background: { type: ColorType.Solid, color: colors.background },
        textColor: colors.text,
      },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid },
      },
      width: chartContainer.clientWidth,
      height: chartContainer.clientHeight,
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: colors.grid,
      },
      timeScale: {
        borderColor: colors.grid,
        timeVisible: true,
      },
    });

    // v5 API: use addSeries with the series class
    candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: colors.upColor,
      downColor: colors.downColor,
      borderUpColor: colors.borderUpColor,
      borderDownColor: colors.borderDownColor,
      wickUpColor: colors.wickUpColor,
      wickDownColor: colors.wickDownColor,
    });

    volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    if (volumeSeries) {
      volumeSeries.priceScale().applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      });
    }

    if (data.length > 0 && candlestickSeries && volumeSeries) {
      candlestickSeries.setData(formatChartData(data));
      volumeSeries.setData(formatVolumeData(data));
      chart.timeScale().fitContent();
    }
  }

  function updateChartTheme() {
    if (!chart) return;

    const isDark = $theme === 'dark';
    const colors = getChartColors(isDark);

    chart.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: colors.background },
        textColor: colors.text,
      },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid },
      },
    });
  }

  function handleResize() {
    if (chart && chartContainer) {
      chart.applyOptions({
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight,
      });
    }
  }

  $effect(() => {
    if (candlestickSeries && volumeSeries && data.length > 0) {
      candlestickSeries.setData(formatChartData(data));
      volumeSeries.setData(formatVolumeData(data));
      chart?.timeScale().fitContent();
    }
  });

  $effect(() => {
    $theme;
    updateChartTheme();
  });

  onMount(() => {
    initChart();
    window.addEventListener('resize', handleResize);
  });

  onDestroy(() => {
    window.removeEventListener('resize', handleResize);
    if (chart) {
      chart.remove();
      chart = null;
    }
  });
</script>

<div bind:this={chartContainer} class="w-full h-full min-h-[400px]"></div>
