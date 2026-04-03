function formatDate(iso) {
  const date = new Date(iso)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function sentimentBadge(sentiment) {
  if (sentiment > 0.1) return { label: 'bullish', color: '#00ff88', bg: '#00ff8820' }
  if (sentiment < -0.1) return { label: 'bearish', color: '#ff4444', bg: '#ff444420' }
  return { label: 'neutral', color: '#888888', bg: '#88888820' }
}

export default function NewsFeed({ news }) {
  const unavailableStyle = {
    background: '#1a1a1a',
    border: '1px solid #2a2a2a',
    borderRadius: '6px',
    padding: '16px',
  }

  if (!news || !news.available) {
    return (
      <div style={unavailableStyle}>
        <div
          style={{
            fontSize: '11px',
            color: '#555',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            marginBottom: '12px',
          }}
        >
          News
        </div>
        <div style={{ color: '#555', fontSize: '13px', fontStyle: 'italic' }}>
          News unavailable
        </div>
      </div>
    )
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div
          style={{
            fontSize: '11px',
            color: '#555',
            textTransform: 'uppercase',
            letterSpacing: '1px',
          }}
        >
          News
        </div>
        <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#555' }}>
          sentiment:{' '}
          <span
            style={{
              color:
                news.sentiment_score > 0.1
                  ? '#00ff88'
                  : news.sentiment_score < -0.1
                    ? '#ff4444'
                    : '#888',
            }}
          >
            {news.sentiment_score >= 0 ? '+' : ''}
            {news.sentiment_score.toFixed(2)}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {news.items.slice(0, 5).map((item, i) => {
          const badge = sentimentBadge(item.sentiment)
          return (
            <div
              key={i}
              style={{
                padding: '10px',
                background: '#111',
                border: '1px solid #2a2a2a',
                borderRadius: '4px',
              }}
            >
              <div style={{ fontSize: '12px', color: '#cccccc', lineHeight: '1.4', marginBottom: '6px' }}>
                {item.title}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', color: '#555' }}>{item.source}</span>
                <span style={{ fontSize: '10px', color: '#444' }}>·</span>
                <span style={{ fontSize: '10px', color: '#555' }}>
                  {formatDate(item.published_at)}
                </span>
                <span
                  style={{
                    marginLeft: 'auto',
                    fontSize: '10px',
                    padding: '1px 6px',
                    borderRadius: '3px',
                    background: badge.bg,
                    color: badge.color,
                    border: `1px solid ${badge.color}44`,
                    fontFamily: 'monospace',
                  }}
                >
                  {badge.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
