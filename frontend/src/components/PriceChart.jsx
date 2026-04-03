import { useEffect, useRef } from 'react'
import { createChart, CandlestickSeries, LineSeries } from 'lightweight-charts'
import { candles } from '../api'

function computeEMA(closes, period) {
  const k = 2 / (period + 1)
  const result = []
  let ema = null
  for (const c of closes) {
    if (ema === null) {
      ema = c
    } else {
      ema = c * k + ema * (1 - k)
    }
    result.push(ema)
  }
  return result
}

export default function PriceChart({ symbol, interval }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#888888',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight || 400,
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#00ff88',
      downColor: '#ff4444',
      borderUpColor: '#00ff88',
      borderDownColor: '#ff4444',
      wickUpColor: '#00ff88',
      wickDownColor: '#ff4444',
    })

    const ema20Series = chart.addSeries(LineSeries, {
      color: '#888888',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    })

    const ema50Series = chart.addSeries(LineSeries, {
      color: '#555555',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    })

    candles(symbol, interval)
      .then(data => {
        if (!Array.isArray(data) || data.length === 0) return

        const candleData = data.map(c => ({
          time: c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
        candleSeries.setData(candleData)

        const closes = data.map(c => c.close)
        const times = data.map(c => c.time)

        const ema20Values = computeEMA(closes, 20)
        const ema50Values = computeEMA(closes, 50)

        ema20Series.setData(
          times.slice(19).map((t, i) => ({ time: t, value: ema20Values[i + 19] }))
        )
        ema50Series.setData(
          times.slice(49).map((t, i) => ({ time: t, value: ema50Values[i + 49] }))
        )
      })
      .catch(err => console.error('[PriceChart] failed to load candles:', err))

    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      chart.applyOptions({ width, height })
    })
    observer.observe(containerRef.current)

    return () => {
      observer.disconnect()
      chart.remove()
    }
  }, [symbol, interval])

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '400px', background: '#1a1a1a' }}
    />
  )
}
