const BADGE_STYLES = {
  BUY: { background: '#00ff88', color: '#000000' },
  SELL: { background: '#ff4444', color: '#000000' },
  HOLD: { background: '#ffaa00', color: '#000000' },
}

export default function DecisionCard({ decision, risk }) {
  if (!decision || !risk) return null

  const action = decision.action
  const badge = BADGE_STYLES[action] || BADGE_STYLES.HOLD
  const confidencePct = Math.round((decision.confidence || 0) * 100)

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
          marginBottom: '16px',
        }}
      >
        Decision
      </div>

      {/* Dominant badge */}
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <span
          style={{
            display: 'inline-block',
            padding: '12px 40px',
            borderRadius: '6px',
            fontSize: '36px',
            fontWeight: 'bold',
            fontFamily: 'monospace',
            letterSpacing: '4px',
            ...badge,
          }}
        >
          {action}
        </span>
      </div>

      {/* Confidence bar */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontSize: '11px', color: '#555' }}>Confidence</span>
          <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#888' }}>
            {confidencePct}%
          </span>
        </div>
        <div
          style={{
            background: '#2a2a2a',
            borderRadius: '3px',
            height: '6px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${confidencePct}%`,
              height: '100%',
              background: badge.background,
              borderRadius: '3px',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Reasoning */}
      {decision.reasoning && (
        <div
          style={{
            fontSize: '12px',
            color: '#888',
            marginBottom: '16px',
            lineHeight: '1.5',
            fontStyle: 'italic',
          }}
        >
          {decision.reasoning}
        </div>
      )}

      {/* Risk levels */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '8px',
          marginBottom: '12px',
          paddingTop: '12px',
          borderTop: '1px solid #2a2a2a',
        }}
      >
        <div>
          <div style={{ fontSize: '10px', color: '#555', marginBottom: '2px' }}>Stop Loss</div>
          <div style={{ fontSize: '13px', fontFamily: 'monospace', color: '#ff4444' }}>
            {risk.stop_loss.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#555', marginBottom: '2px' }}>Take Profit</div>
          <div style={{ fontSize: '13px', fontFamily: 'monospace', color: '#00ff88' }}>
            {risk.take_profit.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#555', marginBottom: '2px' }}>R/R Ratio</div>
          <div style={{ fontSize: '13px', fontFamily: 'monospace', color: '#cccccc' }}>
            {risk.risk_reward.toFixed(2)}x
          </div>
        </div>
      </div>

      {/* Volatility */}
      <div style={{ marginBottom: '12px' }}>
        <span style={{ fontSize: '11px', color: '#555' }}>Volatility: </span>
        <span
          style={{
            fontSize: '11px',
            fontFamily: 'monospace',
            color: risk.volatility === 'HIGH' ? '#ff4444' : '#00ff88',
            fontWeight: 'bold',
          }}
        >
          {risk.volatility}
        </span>
        {risk.position_warning && (
          <span
            style={{
              marginLeft: '8px',
              fontSize: '11px',
              color: '#ffaa00',
              fontFamily: 'monospace',
            }}
          >
            ⚠ {risk.position_warning}
          </span>
        )}
      </div>

      {/* Risk flags */}
      {decision.risk_flags && decision.risk_flags.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {decision.risk_flags.map((flag, i) => (
            <span
              key={i}
              style={{
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '3px',
                background: '#2a2a2a',
                color: '#666',
                border: '1px solid #333',
                fontFamily: 'monospace',
              }}
            >
              {flag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
