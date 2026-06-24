export default function ReflectionCard({ text, onDone }) {
  return (
    <article className="reader-card border-l-4 border-l-success bg-[#F0FFF4]">
      <div className="reader-card-title text-[#1C6A41]">
        <span>💭</span>
        <span>思考题</span>
      </div>
      <p className="card-body">{text}</p>
      {onDone ? (
        <button type="button" className="btn-secondary mt-5" onClick={onDone}>
          思考完了，继续
        </button>
      ) : null}
    </article>
  )
}

