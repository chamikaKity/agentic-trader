import { useState } from 'react'
import PriceChart from './components/PriceChart'

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
const INTERVALS = ['1h', '4h', '1d']

function App() {
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [interval, setInterval] = useState('1h')

  return (
    <div style={{ background: '#0d0d0d', minHeight: '100vh', color: '#cccccc', fontFamily: 'monospace', padding: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <span style={{ color: '#888', fontSize: '13px' }}>Symbol:</span>
        <select
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
          style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#ccc', padding: '4px 8px', fontFamily: 'monospace' }}
        >
          {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <span style={{ color: '#888', fontSize: '13px' }}>Interval:</span>
        <select
          value={interval}
          onChange={e => setInterval(e.target.value)}
          style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#ccc', padding: '4px 8px', fontFamily: 'monospace' }}
        >
          {INTERVALS.map(i => <option key={i} value={i}>{i}</option>)}
        </select>
      </div>
      <PriceChart symbol={symbol} interval={interval} />
    </div>
  )
}

export default App
