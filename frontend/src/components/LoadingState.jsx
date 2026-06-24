export default function LoadingState({ title = '正在加载...', description }) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center px-4 text-center">
      <div>
        <div className="pulse-reading mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-lg bg-[#FFF9F0] text-4xl">
          📖
        </div>
        <div className="text-lg font-semibold text-ink">{title}</div>
        {description ? <div className="mt-2 text-sm text-muted">{description}</div> : null}
      </div>
    </div>
  )
}

