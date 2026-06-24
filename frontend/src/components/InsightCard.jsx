import { useState } from 'react'

export default function InsightCard({ cards = [] }) {
  if (!cards.length) return null

  return (
    <article className="reader-card border-l-4 border-l-danger bg-white">
      <div className="reader-card-title">
        <span>⭐</span>
        <span>知识卡片</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {cards.map((card, index) => (
          <FlipCard key={`${card.front}-${index}`} card={card} />
        ))}
      </div>
    </article>
  )
}

function FlipCard({ card }) {
  const [flipped, setFlipped] = useState(false)

  return (
    <button
      type="button"
      onClick={() => setFlipped((value) => !value)}
      className="min-h-[132px] rounded-lg border border-black/10 bg-soft p-4 text-left transition hover:border-primary/40"
    >
      <div className="flex h-full items-center justify-center text-center">
        {flipped ? (
          <p className="text-sm leading-6 text-ink">{card.back}</p>
        ) : (
          <p className="text-xl font-semibold text-primary">{card.front}</p>
        )}
      </div>
    </button>
  )
}

