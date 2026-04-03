export default function IndicatorsPanel({ indicators }) {
  if (!indicators) return null

  const rsiColor =
    indicators.rsi < 35 ? '#00ff88' : indicators.rsi > 65 ? '#ff4444' : '#888888'

  const macdColor = indicators.macd_histogram >= 0 ? '#00ff88' : '#ff4444'

  const bbBadgeStyle = {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 'bold',
    background:
      indicators.bb_position === 'above'
        ? '#ff444433'
        : indicators.bb_position === 'below'
          ? '#00ff8833'
          : '#88888833',
    color:
      indicators.bb_position === 'above'
        ? '#ff4444'
        : indicators.bb_position === 'below'
          ? '#00ff88'
          : '#888888',
    border: `1px solid ${
      indicators.bb_position === 'above'
        ? '#ff4444'
        : indicators.bb_position === 'below'
          ? '#00ff88'
          : '#555555'
    }`,
  }

  return (
    <div
      style={{
        background: '#1a1a1a',
        border: '1px solid #2a2a2a',
        borderRadius: '6px',
        padding: '16px',
      }}
    >
      <div
        style={{
          fontSize: '11px',
          color: '#555',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          marginBottom: '12px',
        }}
      >
        Indicators
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#555', marginBottom: '4px' }}>RSI (14)</div>
          <div style={{ fontSize: '22px', fontFamily: 'monospace', color: rsiColor, fontWeight: 'bold' }}>
            {indicators.rsi.toFixed(2)}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '11px', color: '#555', marginBottom: '4px' }}>MACD Histogram</div>
          <div style={{ fontSize: '22px', fontFamily: 'monospace', color: macdColor, fontWeight: 'bold' }}>
            {indicators.macd_histogram >= 0 ? '+' : ''}
            {indicators.macd_histogram.toFixed(4)}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '11px', color: '#555', marginBottom: '6px' }}>Bollinger Position</div>
          <span style={bbBadgeStyle}>{indicators.bb_position.toUpperCase()}</span>
        </div>

        <div>
          <div style={{ fontSize: '11px', color: '#555', marginBottom: '4px' }}>ATR (14)</div>
          <div style={{ fontSize: '22px', fontFamily: 'monospace', color: '#cccccc', fontWeight: 'bold' }}>
            {indicators.atr.toFixed(2)}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #2a2a2a', display: 'flex', gap: '24px' }}>
        <div>
          <span style={{ fontSize: '11px', color: '#555' }}>EMA20 </span>
          <span style={{ fontSize: '13px', fontFamily: 'monospace', color: '#888' }}>
            {indicators.ema20.toFixed(2)}
          </span>
        </div>
        <div>
          <span style={{ fontSize: '11px', color: '#555' }}>EMA50 </span>
          <span style={{ fontSize: '13px', fontFamily: 'monospace', color: '#888' }}>
            {indicators.ema50.toFixed(2)}
          </span>
        </div>
        <div>
          <span style={{ fontSize: '11px', color: '#555' }}>Price </span>
          <span style={{ fontSize: '13px', fontFamily: 'monospace', color: '#cccccc' }}>
            {indicators.current_price.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  )
}
