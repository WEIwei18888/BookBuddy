const styles = {
  concept: { border: '#2B4C7E', bg: '#FFFFFF', label: '概念', emoji: '🧠' },
  example: { border: '#4CAF78', bg: '#F8FFF8', label: '例子', emoji: '💡' },
  quote: { border: '#999999', bg: '#F8F8F6', label: '引用', emoji: '📖' },
  comparison: { border: '#7C5CBF', bg: '#F8F5FF', label: '对比', emoji: '⚖️' },
  highlight: { border: '#E85D4A', bg: '#FFF5F5', label: '要点', emoji: '⭐' },
}

export default function ContentCard({ card }) {
  const style = styles[card.type] || styles.concept
  return (
    <article
      className="reader-card border-l-4"
      style={{ borderLeftColor: style.border, background: style.bg }}
    >
      <div className="reader-card-title">
        <span>{card.emoji || style.emoji}</span>
        <span>{style.label}</span>
      </div>
      <p className="card-body">{card.content}</p>
    </article>
  )
}

