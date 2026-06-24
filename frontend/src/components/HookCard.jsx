export default function HookCard({ text }) {
  return (
    <article className="reader-card border-l-4 border-l-amber bg-[#FFF9F0]">
      <div className="reader-card-title text-[#8A5B00]">
        <span>🎣</span>
        <span>开场</span>
      </div>
      <p className="card-body font-medium">{text}</p>
    </article>
  )
}

