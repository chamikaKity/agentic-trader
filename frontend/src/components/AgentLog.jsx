export default function AgentLog({ trace }) {
  if (!trace || trace.length === 0) return null

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
        Agent Log
      </div>
      <div
        style={{
          background: '#0a0a0a',
          borderRadius: '4px',
          padding: '12px',
        }}
      >
        {trace.map((line, i) => (
          <div
            key={i}
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              color: '#00ff88',
              lineHeight: '1.7',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}
          >
            {'> '}{line}
          </div>
        ))}
      </div>
    </div>
  )
}
