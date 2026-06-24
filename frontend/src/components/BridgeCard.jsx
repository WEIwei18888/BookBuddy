export default function BridgeCard({ text, hasNext, onNext, onFinish }) {
  return (
    <article className="reader-card border-l-4 border-l-amber bg-[#FFF9F0]">
      <div className="reader-card-title text-[#8A5B00]">
        <span>🌉</span>
        <span>{hasNext ? '下一节预告' : '完成'}</span>
      </div>
      <p className="card-body">{text}</p>
      <button type="button" className="btn-primary mt-5" onClick={hasNext ? onNext : onFinish}>
        {hasNext ? '继续下一节' : '回到书籍总览'}
      </button>
    </article>
  )
}

