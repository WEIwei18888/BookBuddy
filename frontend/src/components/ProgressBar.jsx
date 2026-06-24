export default function ProgressBar({ value = 0, label, compact = false }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0))

  return (
    <div className="w-full">
      <div className="mb-1.5 flex items-center justify-between gap-3 text-xs text-muted">
        {label ? <span>{label}</span> : <span>阅读进度</span>}
        <span>{Math.round(safeValue)}%</span>
      </div>
      <div className={`w-full overflow-hidden rounded-full bg-soft ${compact ? 'h-2' : 'h-3'}`}>
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${safeValue}%` }}
        />
      </div>
    </div>
  )
}

