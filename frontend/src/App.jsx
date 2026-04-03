import { useState } from 'react'
import { analyze } from './api'
import PriceChart from './components/PriceChart'
import IndicatorsPanel from './components/IndicatorsPanel'
import DecisionCard from './components/DecisionCard'
import NewsFeed from './components/NewsFeed'
import AgentLog from './components/AgentLog'

const INTERVALS = ['1h', '4h', '1d']

export default function App() {
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [interval, setInterval] = useState('1h')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleAnalyse() {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await analyze(symbol, interval)
      setData(result)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        background: '#0d0d0d',
        minHeight: '100vh',
        color: '#cccccc',
        fontFamily: 'monospace',
        padding: '16px',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '20px',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ color: '#555', fontSize: '13px' }}>Symbol</span>
        <input
          type="text"
          value={symbol}
          onChange={e => setSymbol(e.target.value.toUpperCase())}
          style={{
            background: '#1a1a1a',
            border: '1px solid #2a2a2a',
            color: '#cccccc',
            padding: '6px 10px',
            fontFamily: 'monospace',
            fontSize: '13px',
            borderRadius: '4px',
            width: '120px',
            outline: 'none',
          }}
        />
        <span style={{ color: '#555', fontSize: '13px' }}>Interval</span>
        <select
          value={interval}
          onChange={e => setInterval(e.target.value)}
          style={{
            background: '#1a1a1a',
            border: '1px solid #2a2a2a',
            color: '#cccccc',
            padding: '6px 10px',
            fontFamily: 'monospace',
            fontSize: '13px',
            borderRadius: '4px',
            outline: 'none',
          }}
        >
          {INTERVALS.map(i => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
        <button
          onClick={handleAnalyse}
          disabled={loading}
          style={{
            background: loading ? '#2a2a2a' : '#00ff88',
            color: '#000',
            border: 'none',
            padding: '6px 20px',
            fontFamily: 'monospace',
            fontSize: '13px',
            fontWeight: 'bold',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            letterSpacing: '1px',
          }}
        >
          {loading ? 'Analysing...' : 'Analyse'}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div
          style={{
            color: '#555',
            fontFamily: 'monospace',
            fontSize: '13px',
            padding: '40px 0',
            textAlign: 'center',
          }}
        >
          {'> Running pipeline...'}
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          style={{
            background: '#1a0a0a',
            border: '1px solid #ff444444',
            borderRadius: '6px',
            padding: '12px 16px',
            color: '#ff4444',
            fontFamily: 'monospace',
            fontSize: '13px',
            marginBottom: '16px',
          }}
        >
          Error: {error}
        </div>
      )}

      {/* Results */}
      {data && (
        <>
          {/* PriceChart — full width */}
          <div style={{ marginBottom: '16px' }}>
            <PriceChart symbol={symbol} interval={interval} />
          </div>

          {/* 2-column grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '16px',
            }}
          >
            {/* Left: IndicatorsPanel + AgentLog */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <IndicatorsPanel indicators={data.indicators} />
              <AgentLog trace={data.agent_trace} />
            </div>

            {/* Right: DecisionCard + NewsFeed */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <DecisionCard
                decision={data.llm_decision}
                ruleSignal={data.rule_engine?.signal}
                risk={data.risk}
              />
              <NewsFeed news={data.news} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
